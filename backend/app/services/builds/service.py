"""BuildsService: serves popular-base / popular-mod analytics from the scraped artifact.

Reads the POE2-Builds-Scraper artifact (via build_data_loader) and enriches it with this
app's craftable identifiers (via BuildResolver) so the meta connects to crafting: a
trending mod carries its mod_group + tier family + the tier distribution implied by the
rolled values builds actually use.

Singleton, mirroring app.services.market.service.get_market_service().
"""

from __future__ import annotations

from typing import Dict, List, Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.services.builds.build_data_loader import load_build_stats
from app.services.builds.models import BuildStats
from app.services.builds.resolver import BuildResolver, ResolvedBase

logger = get_logger(__name__)


class BuildsService:
    def __init__(self) -> None:
        self._stats: Optional[BuildStats] = None
        self._resolver: Optional[BuildResolver] = None
        self._base_cache: Dict[str, ResolvedBase] = {}
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
