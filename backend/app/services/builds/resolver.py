"""Resolve scraped build data onto this app's craftable item/mod identifiers.

Two jobs:
- Base names: poe.ninja `baseType` is the app's base name (direct lookup), except items
  with socketed runes display a "Runeforged "/"Runemastered " prefix - strip and retry.
- Mod templates: the scraper emits "#"-templated text (ALL numbers -> "#"). The app's
  ModItem.json stat_text is normalized with `_normalize_stat_text`, which only templates
  "(X-Y)" ranges / signed / percent - so a fixed-min mod stays e.g. "Adds 1 to # ...".
  We therefore match on a fully-templated canonical key (all numbers -> "#", lowercased),
  not exact string equality. A template maps to a whole tier family (T1..Tn share text);
  value_samples let us estimate the tier distribution.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

_RUNE_PREFIX = re.compile(r"^(Runeforged|Runemastered|Runebound|Runescribed)\s+")
_NUM = re.compile(r"\d+(?:\.\d+)?")
_JEWELRY = {"ring", "amulet", "belt"}


def canonical(stat_text: str) -> str:
    """All numbers -> '#', collapsed/lowercased - the join key between scraper and app."""
    return re.sub(r"\s+", " ", _NUM.sub("#", stat_text)).strip().lower()


@dataclass
class ResolvedBase:
    input_name: str
    resolved_name: Optional[str]
    category: Optional[str]
    slot: Optional[str]
    resolved: bool
    tags: List[str] = field(default_factory=list)


@dataclass
class ResolvedTier:
    tier: int
    mod_id: Optional[str]
    stat_min: Optional[float]
    stat_max: Optional[float]
    required_ilvl: Optional[int]


@dataclass
class ResolvedMod:
    resolved: bool
    mod_group: Optional[str] = None
    mod_type: Optional[str] = None
    stat_text: Optional[str] = None  # the app's stat_text (e.g. "+# to maximum Mana"), for trade matching
    tiers: List[ResolvedTier] = field(default_factory=list)
    tier_distribution: Dict[int, int] = field(default_factory=dict)  # tier -> count of value_samples


class BuildResolver:
    """Builds a canonical-template index over the app's modifiers once, then resolves."""

    def __init__(self) -> None:
        from app.services.crafting.pob_data_loader import get_pob_data_loader

        loader = get_pob_data_loader()
        try:
            mods = loader.get_all_modifiers_combined()
        except Exception:
            mods = loader.get_all_modifiers()

        self._index: Dict[str, list] = {}
        for m in mods:
            if not m.stat_text:
                continue
            self._index.setdefault(canonical(m.stat_text), []).append(m)
        logger.info("builds: resolver indexed %d mods into %d templates", len(mods), len(self._index))

    # --- bases -------------------------------------------------------------
    def resolve_base(self, base_name: str) -> ResolvedBase:
        from app.schemas.item_bases import get_item_base_by_name

        base = get_item_base_by_name(base_name)
        if base is None:
            stripped = _RUNE_PREFIX.sub("", base_name)
            if stripped != base_name:
                base = get_item_base_by_name(stripped)
        if base is None:
            return ResolvedBase(base_name, None, None, None, False, [])
        return ResolvedBase(base_name, base.name, base.category, base.slot, True, list(base.tags or []))

    # --- mods --------------------------------------------------------------
    def _applicable(self, mod, category: Optional[str], tags: Optional[List[str]]) -> bool:
        if not category:
            return True
        ai = mod.applicable_items or []
        if category in ai:
            return True
        if tags and any(t in ai for t in tags):
            return True
        if "jewellery" in ai and category in _JEWELRY:
            return True
        return False

    def resolve_mod(
        self,
        template: str,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        value_samples: Optional[List[float]] = None,
    ) -> ResolvedMod:
        candidates = self._index.get(canonical(template), [])
        if not candidates:
            return ResolvedMod(resolved=False)

        applicable = [m for m in candidates if self._applicable(m, category, tags)]
        family = applicable or candidates  # fall back to any-category match for mod_group

        # Dedupe to one entry per tier (same family can appear via combined sources).
        by_tier: Dict[int, object] = {}
        for m in sorted(family, key=lambda x: x.tier):
            by_tier.setdefault(m.tier, m)
        tiers = [
            ResolvedTier(
                tier=m.tier, mod_id=m.mod_id, stat_min=m.stat_min,
                stat_max=m.stat_max, required_ilvl=m.required_ilvl,
            )
            for m in sorted(by_tier.values(), key=lambda x: x.tier)
        ]

        distribution = self._tier_distribution(by_tier, value_samples)
        first = next(iter(by_tier.values()))
        return ResolvedMod(
            resolved=True,
            mod_group=getattr(first, "mod_group", None),
            mod_type=getattr(getattr(first, "mod_type", None), "value", None),
            stat_text=getattr(first, "stat_text", None),
            tiers=tiers,
            tier_distribution=distribution,
        )

    @staticmethod
    def _tier_distribution(by_tier: Dict[int, object], value_samples: Optional[List[float]]) -> Dict[int, int]:
        if not value_samples:
            return {}
        dist: Dict[int, int] = {}
        for v in value_samples:
            chosen = None
            for tier, mod in sorted(by_tier.items()):
                ranges = getattr(mod, "stat_ranges", None) or []
                first = ranges[0] if ranges else None
                if first is not None and first.min <= v <= first.max:
                    chosen = tier
                    break
                if first is None and mod.stat_min is not None and mod.stat_max is not None:
                    if mod.stat_min <= v <= mod.stat_max:
                        chosen = tier
                        break
            if chosen is not None:
                dist[chosen] = dist.get(chosen, 0) + 1
        return dist
