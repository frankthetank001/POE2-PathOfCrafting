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
from app.services.builds.build_data_loader import load_build_stats
from app.services.builds.models import BuildStats
from app.services.builds.resolver import BuildResolver, ResolvedBase
from app.services.market.cache import TTLCache

logger = get_logger(__name__)


def _trade_search_url(league: str, base_name: str) -> str:
    """A pathofexile.com/trade2 deep-link pre-filtered to a base type. Built as a plain
    string (no GGG call), so it works even though the trade API 403s our datacenter IP -
    the user's browser opens it from their own IP/session.
    """
    query = {"query": {"status": {"option": "online"}, "type": base_name}, "sort": {"price": "asc"}}
    return (
        f"https://www.pathofexile.com/trade2/search/poe2/{quote(league)}"
        f"?q={quote(json.dumps(query))}"
    )


class BuildsService:
    def __init__(self) -> None:
        self._stats: Optional[BuildStats] = None
        self._resolver: Optional[BuildResolver] = None
        self._base_cache: Dict[str, ResolvedBase] = {}
        self._price_cache: TTLCache = TTLCache(default_ttl=settings.builds_cache_ttl)
        self._initialized = False

    async def initialize(self) -> None:
        if self._initialized:
            return
        self._stats = load_build_stats(settings.builds_league_slug)
        if self._stats is not None:
            self._resolver = BuildResolver()
        self._initialized = True

    @property
    def available(self) -> bool:
        return self._stats is not None and self._resolver is not None

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

    def _mods_for_base(self, base_name: str):
        return sorted(
            (m for m in self._stats.mod_usage if m.base_name == base_name),
            key=lambda m: -m.usage_count,
        )

    async def price_base(self, base_name: str, max_mods: int = 4, league: Optional[str] = None) -> Optional[dict]:
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

        prefix_mods: List = []
        suffix_mods: List = []
        implicit_mods: List = []
        target_mods: List[dict] = []
        ilvl = 81

        for mu in self._mods_for_base(base_name):
            if mu.mod_origin not in ("explicit", "implicit"):
                continue
            if len(prefix_mods) + len(suffix_mods) + len(implicit_mods) >= max_mods:
                break
            rm = self._resolver.resolve_mod(mu.mod_template, rb.category, rb.tags, mu.value_samples)
            if not rm.resolved or not rm.tiers or not rm.stat_text:
                continue
            value = statistics.median(mu.value_samples) if mu.value_samples else rm.tiers[0].stat_min
            if value is None:
                continue
            modal = (max(rm.tier_distribution, key=rm.tier_distribution.get)
                     if rm.tier_distribution else rm.tiers[0].tier)
            tier_obj = next((t for t in rm.tiers if t.tier == modal), rm.tiers[0])
            if tier_obj.required_ilvl:
                ilvl = max(ilvl, tier_obj.required_ilvl)
            mtype = rm.mod_type if rm.mod_type in ("prefix", "suffix", "implicit") else "prefix"
            mod_obj = ItemModifier(
                mod_id=tier_obj.mod_id, name=rm.stat_text, mod_type=ModType(mtype),
                tier=tier_obj.tier, stat_text=rm.stat_text, current_value=float(value),
                mod_group=rm.mod_group, required_ilvl=tier_obj.required_ilvl,
            )
            bucket = {"prefix": prefix_mods, "suffix": suffix_mods, "implicit": implicit_mods}[mtype]
            cap = 1 if mtype == "implicit" else 3
            if len(bucket) >= cap:
                continue
            bucket.append(mod_obj)
            target_mods.append({
                "stat_text": rm.stat_text, "value": float(value), "tier": tier_obj.tier,
                "mod_type": mtype, "origin": mu.mod_origin, "usage_pct": mu.usage_pct,
            })

        item = CraftableItem(
            base_name=rb.resolved_name or base_name, base_category=rb.category, slot=rb.slot,
            rarity=ItemRarity.RARE, item_level=ilvl,
            implicit_mods=implicit_mods, prefix_mods=prefix_mods, suffix_mods=suffix_mods,
        )

        league_name = league or self._stats.league
        # Always available (plain URL, no GGG call) so the buy path works despite the IP block.
        trade_search_url = _trade_search_url(league_name, rb.resolved_name or base_name)

        # The trade2 API 403s datacenter IPs, so server-side pricing only works off a
        # non-blocked IP. An empty trade-stats cache means we couldn't reach it - in that
        # case report "pricing unavailable" honestly rather than faking a scarcity verdict.
        from app.services.market import item_pricer as ip_module

        market = None
        trade_ready = False
        try:
            pricer = await get_item_pricer()
            trade_ready = bool(getattr(ip_module, "_trade_stats_cache", None))
            if trade_ready:
                est = await pricer.estimate_price(item, league=league_name)
                if est is not None:
                    market = {
                        "chaos_floor": round(est.median_price, 1),
                        "divine": round(est.divine_value, 2) if est.divine_value else None,
                        "exalted": round(est.exalted_value, 1) if est.exalted_value else None,
                        "num_listings": est.num_listings,
                        "confidence": est.confidence,
                        "trade_url": est.trade_url or trade_search_url,
                    }
        except Exception as e:  # rate limits, trade-API hiccups - best-effort
            logger.warning("builds: pricing failed for %s: %s", base_name, e)
            market = {"error": str(e)}

        craftable = bool(target_mods) and len(prefix_mods) <= 3 and len(suffix_mods) <= 3
        n_listings = (market or {}).get("num_listings", 0) if market else 0
        if not trade_ready:
            verdict, message = "pricing_unavailable", (
                "Live market pricing isn't reachable from the server (the trade API blocks "
                "datacenter IPs). Open the trade search to check current prices in your browser."
            )
        elif not market or market.get("error") or not n_listings:
            verdict, message = "craft_candidate", (
                "Few/no market listings for this mod combination - a craft candidate "
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
            "item_level": ilvl,
            "trade_search_url": trade_search_url,
            "target_mods": target_mods,
            "prefixes": len(prefix_mods),
            "suffixes": len(suffix_mods),
            "craftable": craftable,
            "priced": bool(market and not market.get("error") and n_listings),
            "market": market,
            "verdict": verdict,
            "message": message,
            "note": ("Buy price is live market data. Precise craft (gamble) cost is not yet "
                     "modelled; use price + listing scarcity as the buy-vs-craft signal."),
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
