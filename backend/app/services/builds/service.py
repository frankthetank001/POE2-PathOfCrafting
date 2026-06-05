"""BuildsService: serves popular-base / popular-mod analytics from the scraped artifact.

Reads the POE2-Builds-Scraper artifact (via build_data_loader) and enriches it with this
app's craftable identifiers (via BuildResolver) so the meta connects to crafting: a
trending mod carries its mod_group + tier family + the tier distribution implied by the
rolled values builds actually use.

Singleton, mirroring app.services.market.service.get_market_service().
"""

from __future__ import annotations

import json
import statistics
from typing import Dict, List, Optional
from urllib.parse import quote

from app.core.config import settings
from app.core.logging import get_logger
from app.services.builds.build_data_loader import load_build_stats, load_builds_artifact
from app.services.builds.models import Build, BuildItem, BuildsArtifact, BuildStats
from app.services.builds.resolver import BuildResolver, ResolvedBase
from app.services.market.cache import TTLCache

logger = get_logger(__name__)


# "securable" = instant-buyout-only, matching the price engine and the UI's "instant buyout only".
_TRADE_STATUS = "securable"


def _trade2_url(league: str, query: dict) -> str:
    return (
        f"https://www.pathofexile.com/trade2/search/poe2/{quote(league)}"
        f"?q={quote(json.dumps(query))}"
    )


def _trade_search_url(league: str, base_name: str, rarity: Optional[str] = None) -> str:
    """A pathofexile.com/trade2 deep-link pre-filtered to a base type (and optionally a
    rarity: 'normal' for a raw white base, 'magic' for a partial). Built as a plain string
    (no GGG call), so it works even though the trade API 403s our datacenter IP - the user's
    browser opens it from their own IP/session.
    """
    query: dict = {"query": {"status": {"option": _TRADE_STATUS}, "type": base_name}, "sort": {"price": "asc"}}
    if rarity:
        query["query"]["filters"] = {"type_filters": {"filters": {"rarity": {"option": rarity}}}}
    return _trade2_url(league, query)


def _stat_group(stat_ids: Optional[list]) -> Optional[dict]:
    """A trade2 stat GROUP for ONE logical mod. A display text can map to SEVERAL trade stat
    ids (e.g. '# to Spirit' -> two distinct ids; ~24 common mods are ambiguous) - so use a
    count>=1 group, which matches if ANY variant is present, exactly like the price engine
    (item_pricer line ~851). Picking only ids[0] silently matched the wrong variant and
    returned nothing. No roll-min: a deep-link should FIND the mod, not gate on an exact roll
    (over-tight mins also dropped valid listings)."""
    ids = [s for s in (stat_ids or []) if s]
    if not ids:
        return None
    if len(ids) == 1:
        return {"type": "and", "filters": [{"id": ids[0]}]}
    return {"type": "count", "value": {"min": 1}, "filters": [{"id": s} for s in ids]}


def _stats_trade_url(league: str, base_name: str, groups: list, rarity: Optional[str] = None) -> str:
    """A trade2 deep-link for a base + a list of stat groups (one per logical mod) + rarity."""
    groups = [g for g in (groups or []) if g]
    query: dict = {"query": {"status": {"option": _TRADE_STATUS}, "type": base_name}, "sort": {"price": "asc"}}
    if groups:
        query["query"]["stats"] = groups
    if rarity:
        query["query"]["filters"] = {"type_filters": {"filters": {"rarity": {"option": rarity}}}}
    return _trade2_url(league, query)


class BuildsService:
    def __init__(self) -> None:
        self._stats: Optional[BuildStats] = None
        self._builds_artifact: Optional[BuildsArtifact] = None
        self._builds_by_id: Dict[str, Build] = {}
        self._resolver: Optional[BuildResolver] = None
        self._base_cache: Dict[str, ResolvedBase] = {}
        self._price_cache: TTLCache = TTLCache(default_ttl=settings.builds_cache_ttl)
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._stats = load_build_stats(settings.builds_league_slug)
        self._builds_artifact = load_builds_artifact(settings.builds_league_slug)
        # The resolver indexes the crafting mod pool; it's useful for either artifact.
        if self._stats is not None or self._builds_artifact is not None:
            self._resolver = BuildResolver()
        if self._builds_artifact is not None:
            self._builds_by_id = {b.id: b for b in self._builds_artifact.builds}
        self._initialized = True

    @property
    def available(self) -> bool:
        """Aggregate meta endpoints (meta/trending/base/price) need the stats artifact."""
        return self._stats is not None and self._resolver is not None

    @property
    def builds_available(self) -> bool:
        """The builds-browser endpoints need the per-build sample artifact."""
        return self._builds_artifact is not None and self._resolver is not None

    def _resolve_base(self, name: str) -> ResolvedBase:
        cached = self._base_cache.get(name)
        if cached is None:
            cached = self._resolver.resolve_base(name)
            self._base_cache[name] = cached
        return cached

    # --- queries -----------------------------------------------------------
    def get_meta(self) -> Optional[dict]:
        if not self.available:
            return None
        s = self._stats
        resolved_bases = sum(1 for b in s.base_usage if self._resolve_base(b.base_name).resolved)
        return {
            "league": s.league,
            "league_slug": s.league_slug,
            "snapshot_version": s.snapshot_version,
            "scraped_at": s.scraped_at,
            "sample_size": s.sample_size,
            "roster_size": s.roster_size,
            "base_count": len(s.base_usage),
            "mod_count": len(s.mod_usage),
            "bases_resolved": resolved_bases,
            "disclaimer": s.disclaimer,
        }

    def trending_bases(self, slot: Optional[str] = None, limit: int = 50) -> List[dict]:
        if not self.available:
            return []
        out: List[dict] = []
        for b in self._stats.base_usage:
            if slot and b.slot != slot:
                continue
            rb = self._resolve_base(b.base_name)
            out.append({
                "base_name": b.base_name,
                "slot": b.slot,
                "usage_count": b.usage_count,
                "usage_pct": b.usage_pct,
                "rarity_mix": b.rarity_mix,
                "common_skills": b.common_skills,
                "category": rb.category,
                "resolves_in_app": rb.resolved,
            })
            if len(out) >= limit:
                break
        return out

    def trending_mods(
        self, base_name: Optional[str] = None, origin: Optional[str] = None, limit: int = 50
    ) -> List[dict]:
        if not self.available:
            return []
        out: List[dict] = []
        for m in self._stats.mod_usage:
            if base_name and m.base_name != base_name:
                continue
            if origin and m.mod_origin != origin:
                continue
            rb = self._resolve_base(m.base_name)
            rm = self._resolver.resolve_mod(
                m.mod_template, rb.category, rb.tags, m.value_samples
            )
            top_tier = min(rm.tier_distribution, key=rm.tier_distribution.get) if rm.tier_distribution else None
            modal_tier = (
                max(rm.tier_distribution.items(), key=lambda kv: kv[1])[0]
                if rm.tier_distribution else None
            )
            out.append({
                "base_name": m.base_name,
                "slot": m.slot,
                "mod_template": m.mod_template,
                "mod_origin": m.mod_origin,
                "usage_count": m.usage_count,
                "usage_pct": m.usage_pct,
                "resolved": rm.resolved,
                "mod_group": rm.mod_group,
                "mod_type": rm.mod_type,
                "tier_count": len(rm.tiers),
                "best_tier_seen": top_tier,
                "modal_tier": modal_tier,
                "tier_distribution": rm.tier_distribution,
            })
            if len(out) >= limit:
                break
        return out

    def base_detail(self, base_name: str, mod_limit: int = 30) -> Optional[dict]:
        if not self.available:
            return None
        base_row = next((b for b in self._stats.base_usage if b.base_name == base_name), None)
        if base_row is None:
            return None
        rb = self._resolve_base(base_name)
        mods = self.trending_mods(base_name=base_name, limit=mod_limit)
        return {
            "base_name": base_name,
            "slot": base_row.slot,
            "category": rb.category,
            "resolves_in_app": rb.resolved,
            "usage_count": base_row.usage_count,
            "usage_pct": base_row.usage_pct,
            "rarity_mix": base_row.rarity_mix,
            "common_skills": base_row.common_skills,
            "mods": mods,
        }

    # --- builds browser ----------------------------------------------------
    def builds_meta(self) -> Optional[dict]:
        if not self.builds_available:
            return None
        a = self._builds_artifact
        return {
            "league": a.league,
            "league_slug": a.league_slug,
            "snapshot_version": a.snapshot_version,
            "scraped_at": a.scraped_at,
            "sample_size": a.sample_size,
            "roster_size": a.roster_size,
            "disclaimer": a.disclaimer,
        }

    @staticmethod
    def _top_skill(b: Build) -> Optional[dict]:
        if not b.main_skills:
            return None
        s = max(b.main_skills, key=lambda x: x.dps)
        return {"name": s.name, "dps": s.dps}

    def _build_summary(self, b: Build) -> dict:
        uniques = [it.name for it in b.items if it.rarity == "unique" and it.name]
        return {
            "id": b.id,
            "character": b.character,
            "account": b.account,
            "level": b.level,
            "base_class": b.base_class,
            "ascendancy": b.ascendancy,
            "main_skill": self._top_skill(b),
            "life": b.defense.life,
            "energy_shield": b.defense.energy_shield,
            "ehp": b.defense.ehp,
            "item_count": len(b.items),
            "notable_uniques": uniques[:4],
            "poeninja_url": b.poeninja_url,
            "has_pob": bool(b.pob_export),
        }

    def list_builds(
        self,
        ascendancy: Optional[str] = None,
        base_class: Optional[str] = None,
        skill: Optional[str] = None,
        q: Optional[str] = None,
        limit: int = 60,
        offset: int = 0,
    ) -> dict:
        """Paginated build summaries with optional class/skill/text filters."""
        if not self.builds_available:
            return {"total": 0, "builds": [], "ascendancies": [], "skills": []}

        builds = self._builds_artifact.builds
        ql = q.lower().strip() if q else None
        sl = skill.lower().strip() if skill else None

        def matches(b: Build) -> bool:
            if ascendancy and b.ascendancy != ascendancy:
                return False
            if base_class and b.base_class != base_class:
                return False
            skill_names = [s.name.lower() for s in b.main_skills]
            if sl and not any(sl in n for n in skill_names):
                return False
            if ql:
                hay = " ".join([
                    b.character.lower(), (b.ascendancy or "").lower(),
                    (b.base_class or "").lower(), " ".join(skill_names),
                    " ".join((it.name or "").lower() for it in b.items),
                ])
                if ql not in hay:
                    return False
            return True

        filtered = [b for b in builds if matches(b)]
        # Sort by level then top DPS so strong, complete builds lead.
        filtered.sort(key=lambda b: (b.level, (self._top_skill(b) or {}).get("dps", 0)), reverse=True)

        # Facets are computed over the FULL set so the filter UI stays stable.
        ascendancies = sorted({b.ascendancy for b in builds if b.ascendancy})
        skills = sorted({s.name for b in builds for s in b.main_skills})

        page = filtered[offset:offset + limit]
        return {
            "total": len(filtered),
            "builds": [self._build_summary(b) for b in page],
            "ascendancies": ascendancies,
            "skills": skills,
        }

    def _resolve_item(self, item: BuildItem) -> dict:
        """A build item with each mod enriched (where it resolves) with mod_group/tier/mod_id."""
        rb = self._resolve_base(item.base_type)
        mods_out: List[dict] = []
        for mod in item.mods:
            entry = {
                "text": mod.text, "origin": mod.origin, "values": mod.values,
                "resolved": False, "mod_group": None, "mod_type": None,
                "tier": None, "mod_id": None,
            }
            # Resolve against the crafting pool; pass the rolled value to pin the exact tier.
            rm = self._resolver.resolve_mod(
                mod.text, rb.category, rb.tags, mod.values or None
            )
            if rm.resolved:
                if rm.tier_distribution:
                    tier = max(rm.tier_distribution.items(), key=lambda kv: kv[1])[0]
                else:
                    tier = rm.tiers[0].tier if rm.tiers else None
                tier_obj = next((t for t in rm.tiers if t.tier == tier), None)
                entry.update({
                    "resolved": True, "mod_group": rm.mod_group, "mod_type": rm.mod_type,
                    "tier": tier, "mod_id": tier_obj.mod_id if tier_obj else None,
                })
            mods_out.append(entry)
        return {
            "slot": item.slot,
            "name": item.name,
            "base_type": item.base_type,
            "resolved_base": rb.resolved_name,
            "category": rb.category,
            "resolves_in_app": rb.resolved,
            "rarity": item.rarity,
            "item_level": item.item_level,
            "icon": item.icon,
            "corrupted": item.corrupted,
            "runes": item.runes,
            "mods": mods_out,
        }

    def get_build(self, build_id: str) -> Optional[dict]:
        if not self.builds_available:
            return None
        b = self._builds_by_id.get(build_id)
        if b is None:
            return None
        return {
            "id": b.id,
            "account": b.account,
            "character": b.character,
            "level": b.level,
            "base_class": b.base_class,
            "ascendancy": b.ascendancy,
            "main_skills": [
                {"name": s.name, "dps": s.dps, "supports": s.supports} for s in b.main_skills
            ],
            "defense": b.defense.model_dump(),
            "items": [self._resolve_item(it) for it in b.items],
            "poeninja_url": b.poeninja_url,
            "pob_export": b.pob_export,
            "updated_utc": b.updated_utc,
        }

    def _mods_for_base(self, base_name: str):
        return sorted(
            (m for m in self._stats.mod_usage if m.base_name == base_name),
            key=lambda m: -m.usage_count,
        )

    @staticmethod
    def _market_from_estimate(est, fallback_url: str) -> dict:
        return {
            "chaos_floor": round(est.median_price, 1),
            "divine": round(est.divine_value, 2) if est.divine_value else None,
            "exalted": round(est.exalted_value, 1) if est.exalted_value else None,
            "num_listings": est.num_listings,
            "confidence": est.confidence,
            # Prefer the self-contained ?q= deep-link over the pricer's search-id URL: search ids
            # EXPIRE on GGG's side (a cached price's link goes dead) and the id URL also carries an
            # unescaped league space. The ?q= link is durable and carries the same filters.
            "trade_url": fallback_url or est.trade_url,
        }

    def _select_meta_mods(self, base_name: str, rb, max_mods: int, tier_mode: str = "modal"):
        """The base's meta mods as ItemModifiers + target_mod dicts + the ilvl the set needs.
        tier_mode 'modal' = the most common tier builds roll (a TYPICAL item); 'best' = the
        best tier the meta actually rolls (a GOOD, craft-worthy item)."""
        from app.schemas.crafting import ItemModifier, ModType

        prefix_mods: List = []
        suffix_mods: List = []
        implicit_mods: List = []
        target_mods: List[dict] = []
        ilvl = 81
        for mu in self._mods_for_base(base_name):
            if mu.mod_origin not in ("explicit", "implicit"):
                continue
            # max_mods caps EXPLICIT affixes (3 prefix + 3 suffix on a rare); the implicit is
            # extra and doesn't consume a slot.
            if len(prefix_mods) + len(suffix_mods) >= max_mods:
                break
            rm = self._resolver.resolve_mod(mu.mod_template, rb.category, rb.tags, mu.value_samples)
            if not rm.resolved or not rm.tiers or not rm.stat_text:
                continue
            if tier_mode == "best":
                chosen = min(rm.tier_distribution) if rm.tier_distribution else min(t.tier for t in rm.tiers)
            else:
                chosen = (max(rm.tier_distribution, key=rm.tier_distribution.get)
                          if rm.tier_distribution else rm.tiers[0].tier)
            tier_obj = next((t for t in rm.tiers if t.tier == chosen), rm.tiers[0])
            if tier_mode == "best" and tier_obj.stat_max is not None:
                value = tier_obj.stat_max  # a good roll = the top of that tier
            elif mu.value_samples:
                value = statistics.median(mu.value_samples)
            else:
                value = tier_obj.stat_min
            if value is None:
                continue
            if tier_obj.required_ilvl:
                ilvl = max(ilvl, tier_obj.required_ilvl)
            mtype = rm.mod_type if rm.mod_type in ("prefix", "suffix", "implicit") else "prefix"
            bucket = {"prefix": prefix_mods, "suffix": suffix_mods, "implicit": implicit_mods}[mtype]
            cap = 1 if mtype == "implicit" else 3
            if len(bucket) >= cap:
                continue
            bucket.append(ItemModifier(
                mod_id=tier_obj.mod_id, name=rm.stat_text, mod_type=ModType(mtype),
                tier=tier_obj.tier, stat_text=rm.stat_text, current_value=float(value),
                mod_group=rm.mod_group, required_ilvl=tier_obj.required_ilvl,
            ))
            target_mods.append({
                "stat_text": rm.stat_text, "value": float(value), "tier": tier_obj.tier,
                "mod_type": mtype, "origin": mu.mod_origin, "usage_pct": mu.usage_pct,
            })
        return prefix_mods, suffix_mods, implicit_mods, target_mods, ilvl

    async def _price_white_base(self, pricer, resolved_base, rb, ilvl, league, fallback_url):
        """Price the raw white base at a target ilvl (rarity=normal, buyout-only). estimate_price
        bails on a mod-less item, so build the base query directly + reuse the price calc."""
        from app.schemas.crafting import CraftableItem, ItemRarity
        try:
            item = CraftableItem(base_name=resolved_base, base_category=rb.category, slot=rb.slot,
                                 rarity=ItemRarity.NORMAL, item_level=ilvl)
            q = pricer._build_query(item, {}, 0.8, None, None, True, True, None, None, "securable")
            q["query"]["type"] = resolved_base  # the specific base, not just the category
            listings, qid = await pricer._trade_client.search_and_fetch(q, league, max_results=20)
            if not listings:
                return None
            url = pricer._trade_client.build_trade_url(qid, league) if qid else fallback_url
            est = await pricer._calculate_price(listings, {}, 0.8, url, item, {})
            return self._market_from_estimate(est, fallback_url) if est else None
        except Exception as e:
            logger.warning("builds: white-base pricing failed for %s: %s", resolved_base, e)
            return None

    async def price_base(self, base_name: str, max_mods: int = 6, league: Optional[str] = None) -> Optional[dict]:
        """Buy-vs-craft signal for a popular base: price a Rare with its top meta mods on
        the live market, plus craftability. NOTE: the buy price is real market data; the
        craft (gamble) cost is not modelled - listing scarcity is the craft-vs-buy signal.
        """
        if not self.available:
            return None
        cache_key = f"{base_name}|{max_mods}"
        cached = self._price_cache.get(cache_key)
        if cached is not None:
            return cached

        # Local imports: heavy crafting/market modules, only needed when pricing.
        from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType
        from app.schemas.item_bases import get_item_base_by_name
        from app.services.market.item_pricer import get_item_pricer

        rb = self._resolve_base(base_name)
        if not rb.resolved or not rb.category:
            result = {"base_name": base_name, "priced": False, "craftable": False,
                      "verdict": "unknown", "note": "Base not matched to a craftable item.",
                      "target_mods": [], "market": None,
                      "trade_search_url": _trade_search_url(league or self._stats.league, base_name)}
            self._price_cache.set(cache_key, result)
            return result

        from app.schemas.crafting import CraftableItem, ItemRarity

        # DISPLAY: the full decked-out meta rare (up to 6 affixes + implicit) at best tiers.
        _, _, _, good_mods, gd_ilvl = self._select_meta_mods(base_name, rb, max_mods, "best")
        # Dedup: two mod templates can resolve to the same stat text (e.g. flat + hybrid both
        # grant attributes), which would show the same line twice with different thresholds.
        _seen_mods: set = set()
        good_mods = [m for m in good_mods if not (m["stat_text"] in _seen_mods or _seen_mods.add(m["stat_text"]))]
        # PRICE: only the ~4 key affixes - a full 6-mod search is too strict (almost nobody lists
        # an item with those EXACT 6 mods) and returns no listings. GOOD = best tiers, TYPICAL = modal.
        gd_pre, gd_suf, gd_imp, _, _ = self._select_meta_mods(base_name, rb, 4, "best")
        tp_pre, tp_suf, tp_imp, _, tp_ilvl = self._select_meta_mods(base_name, rb, 4, "modal")

        def _rare(pre, suf, imp, lvl):
            return CraftableItem(
                base_name=rb.resolved_name or base_name, base_category=rb.category, slot=rb.slot,
                rarity=ItemRarity.RARE, item_level=lvl, implicit_mods=imp, prefix_mods=pre, suffix_mods=suf,
            )

        good_item = _rare(gd_pre, gd_suf, gd_imp, gd_ilvl)
        typical_item = _rare(tp_pre, tp_suf, tp_imp, tp_ilvl)

        league_name = league or self._stats.league
        resolved_base = rb.resolved_name or base_name
        # Always available (plain URLs, no GGG call) so the buy paths work despite the IP block.
        trade_search_url = _trade_search_url(league_name, resolved_base)
        base_trade_url = _trade_search_url(league_name, resolved_base, "normal")  # raw white base
        magic_trade_url = _trade_search_url(league_name, resolved_base, "magic")  # partial / blue base

        from app.services.market import item_pricer as ip_module

        # Magic "partial": a blue base carrying the GOOD top prefix + suffix (pre-slammed).
        magic_prefix = gd_pre[:1]
        magic_suffix = gd_suf[:1]
        magic_mods = [
            tm for tm in good_mods
            if (tm["mod_type"] == "prefix" and magic_prefix and tm["stat_text"] == magic_prefix[0].stat_text)
            or (tm["mod_type"] == "suffix" and magic_suffix and tm["stat_text"] == magic_suffix[0].stat_text)
        ]

        market = None           # GOOD finished rare (headline)
        market_typical = None   # typical/modal finished rare
        magic_market = None     # magic partial
        base_market = None      # raw white base at the target ilvl
        magic_variants: List[dict] = []  # blue-base mod combos to flip through
        rare_q_url = trade_search_url    # self-contained ?q= link for the rare, filled below
        magic_link = magic_trade_url
        trade_ready = False
        try:
            pricer = await get_item_pricer()
            trade_ready = bool(getattr(ip_module, "_trade_stats_cache", None))
            if trade_ready:
                # 1) Build the self-contained ?q= deep-links FIRST (pure stat-id string work, no
                #    network). These used to be built AFTER the price calls, so a single rate-limit
                #    exception wiped every per-mod link and all magic variants.
                rare_groups: List[dict] = []
                for tm in good_mods:
                    grp = _stat_group(pricer._match_stat_to_trade_ids(tm["stat_text"]))
                    if grp is None:
                        continue
                    tm["trade_url"] = _stats_trade_url(league_name, resolved_base, [grp])
                    # The rare link keeps to the top ~3 key mods - requiring all 6 would be too
                    # strict to return listings.
                    if len(rare_groups) < 3 and tm["origin"] in ("explicit", "implicit"):
                        rare_groups.append(grp)
                if rare_groups:
                    rare_q_url = _stats_trade_url(league_name, resolved_base, rare_groups, "rare")
                # Magic "partial" variants: each good prefix x good suffix combo as a magic-rarity
                # search, so the UI can flip through real blue-base examples.
                gp = [tm for tm in good_mods if tm["mod_type"] == "prefix"][:3]
                gs = [tm for tm in good_mods if tm["mod_type"] == "suffix"][:3]
                for p in gp:
                    for s in gs:
                        groups = [
                            _stat_group(pricer._match_stat_to_trade_ids(p["stat_text"])),
                            _stat_group(pricer._match_stat_to_trade_ids(s["stat_text"])),
                        ]
                        groups = [g for g in groups if g]
                        if groups:
                            magic_variants.append({
                                "mods": [p["stat_text"], s["stat_text"]],
                                "trade_url": _stats_trade_url(league_name, resolved_base, groups, "magic"),
                            })
                magic_variants = magic_variants[:6]
                if magic_variants:
                    magic_link = magic_variants[0]["trade_url"]

                # 2) Then price (best-effort). "securable" = instant-buyout-only listings (the
                #    default "any" includes offline/bait listings that crater the floor). A
                #    rate-limit here no longer destroys the links built above.
                est = await pricer.estimate_price(good_item, league=league_name, purchase_type="securable")
                if est is not None:
                    market = self._market_from_estimate(est, rare_q_url)
                tyest = await pricer.estimate_price(typical_item, league=league_name, purchase_type="securable")
                if tyest is not None:
                    market_typical = self._market_from_estimate(tyest, rare_q_url)
                if magic_prefix or magic_suffix:
                    magic_item = CraftableItem(
                        base_name=resolved_base, base_category=rb.category, slot=rb.slot,
                        rarity=ItemRarity.MAGIC, item_level=gd_ilvl,
                        prefix_mods=magic_prefix, suffix_mods=magic_suffix,
                    )
                    mest = await pricer.estimate_price(magic_item, league=league_name, purchase_type="securable")
                    if mest is not None:
                        magic_market = self._market_from_estimate(mest, magic_link)
                base_market = await self._price_white_base(
                    pricer, resolved_base, rb, gd_ilvl, league_name, base_trade_url
                )
        except Exception as e:  # rate limits, trade-API hiccups - best-effort
            logger.warning("builds: pricing failed for %s: %s", base_name, e)
            if market is None:
                market = {"error": str(e)}

        # Every meta mod gets at least the base-type search as a fallback link.
        for tm in good_mods:
            tm.setdefault("trade_url", trade_search_url)

        craftable = bool(good_mods) and len(gd_pre) <= 3 and len(gd_suf) <= 3
        n_listings = (market or {}).get("num_listings", 0) if market else 0
        market_errored = bool(market and market.get("error"))
        if not good_mods:
            # e.g. a base seen only as a unique in the sample - there is no rare meta-mod pool.
            verdict, message = "no_meta_data", (
                "Not enough rare-item data for this base in the current sample (it shows up "
                "mostly as a unique), so there's no meta mod set to price or craft toward."
            )
        elif not trade_ready or market_errored:
            verdict, message = "pricing_unavailable", (
                "Live market pricing isn't reachable right now (the trade API blocks datacenter "
                "IPs and is rate-limited). Use the trade links to check current prices in your browser."
            )
        elif not market or not n_listings:
            verdict, message = "craft_candidate", (
                "Few/no buyout listings for a good roll - a craft candidate "
                "(the meta mods fit a Rare). Click through to verify on trade."
            )
        elif n_listings >= 8 and (market.get("confidence") in ("high", "medium")):
            verdict, message = "buy", "Plentiful on the market - buying is straightforward."
        else:
            verdict, message = "available", "Listed, but limited supply."

        result = {
            "base_name": base_name,
            "resolved_name": rb.resolved_name,
            "category": rb.category,
            "slot": rb.slot,
            "item_level": gd_ilvl,
            "base_ilvl": gd_ilvl,
            "trade_search_url": trade_search_url,
            "base_trade_url": base_trade_url,
            "magic_trade_url": magic_trade_url,
            "target_mods": good_mods,
            "magic_mods": magic_mods,
            "magic_variants": magic_variants,
            "prefixes": len(gd_pre),
            "suffixes": len(gd_suf),
            "craftable": craftable,
            "priced": bool(market and not market.get("error") and n_listings),
            "market": market,
            "market_typical": market_typical,
            "magic_market": magic_market,
            "base_market": base_market,
            "verdict": verdict,
            "message": message,
            "note": ("Prices are live buyout listings. 'Good' = the best tiers the meta rolls; "
                     "'typical' = the most common roll. Craft (gamble) cost is not modelled."),
        }
        self._price_cache.set(cache_key, result)
        return result


# -----------------------------------------------------------------------------
# Singleton
# -----------------------------------------------------------------------------
_builds_service: Optional[BuildsService] = None


async def get_builds_service() -> BuildsService:
    global _builds_service
    if _builds_service is None:
        _builds_service = BuildsService()
        await _builds_service.initialize()
    return _builds_service
