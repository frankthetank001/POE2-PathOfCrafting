"""Models for the popular-builds usage artifact produced by POE2-Builds-Scraper.

Mirrors that repo's `build-stats-<slug>-<version>.json` output. The scraper emits
markup-free, value-templated mod text (`mod_template`, e.g. "+# to maximum Mana") but no
mod_id/tier; this app resolves those against its own ModItem.json at query time.
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, Field


class BaseUsage(BaseModel):
    base_name: str
    slot: str
    usage_count: int = 0
    usage_pct: float = 0.0
    rarity_mix: Dict[str, int] = Field(default_factory=dict)
    common_skills: List[str] = Field(default_factory=list)


class ModUsage(BaseModel):
    base_name: str
    slot: str
    mod_template: str
    mod_origin: str  # explicit | implicit | rune | crafted | fractured | desecrated | enchant
    usage_count: int = 0
    usage_pct: float = 0.0
    value_samples: List[float] = Field(default_factory=list)


class BuildStats(BaseModel):
    league: str
    league_slug: str
    snapshot_version: str
    snapshot_name: str
    scraped_at: str
    sample_size: int
    roster_size: int = 0
    base_usage: List[BaseUsage] = Field(default_factory=list)
    mod_usage: List[ModUsage] = Field(default_factory=list)
    disclaimer: str = ""
