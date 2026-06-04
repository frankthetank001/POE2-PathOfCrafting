"""Models for the popular-builds usage artifact produced by POE2-Builds-Scraper.

Mirrors that repo's `build-stats-<slug>-<version>.json` output. The scraper emits
markup-free, value-templated mod text (`mod_template`, e.g. "+# to maximum Mana") but no
mod_id/tier; this app resolves those against its own ModItem.json at query time.
"""

from __future__ import annotations

from typing import Dict, List, Optional

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


# ---------------------------------------------------------------------------
# Builds-browser artifact (builds-<slug>.json) - a representative SAMPLE of real
# builds with their gear/skills/defenses/links. Mirrors POE2-Builds-Scraper's
# BuildsArtifact exactly (snake_case). Mod `text` is markup-stripped but NOT
# templated (numbers intact); the app resolves tier/mod_id from `text` at query time.
# ---------------------------------------------------------------------------
class BuildItemMod(BaseModel):
    text: str
    origin: str  # explicit | implicit | rune | crafted | fractured | desecrated | enchant
    values: List[float] = Field(default_factory=list)


class BuildItem(BaseModel):
    slot: str
    name: Optional[str] = None
    base_type: str
    rarity: str  # normal | magic | rare | unique
    item_level: int = 0
    icon: Optional[str] = None
    corrupted: bool = False
    mods: List[BuildItemMod] = Field(default_factory=list)
    runes: List[str] = Field(default_factory=list)


class BuildSkill(BaseModel):
    name: str
    dps: int = 0
    supports: List[str] = Field(default_factory=list)


class BuildDefense(BaseModel):
    life: int = 0
    energy_shield: int = 0
    mana: int = 0
    spirit: int = 0
    ehp: int = 0
    fire_res: int = 0
    cold_res: int = 0
    lightning_res: int = 0
    chaos_res: int = 0


class Build(BaseModel):
    id: str
    account: str
    character: str
    level: int = 0
    base_class: Optional[str] = None
    ascendancy: Optional[str] = None
    main_skills: List[BuildSkill] = Field(default_factory=list)
    defense: BuildDefense = Field(default_factory=BuildDefense)
    items: List[BuildItem] = Field(default_factory=list)
    poeninja_url: str = ""
    pob_export: Optional[str] = None
    updated_utc: str = ""


class BuildsArtifact(BaseModel):
    league: str
    league_slug: str
    snapshot_version: str
    snapshot_name: str
    scraped_at: str
    sample_size: int
    roster_size: int = 0
    builds: List[Build] = Field(default_factory=list)
    disclaimer: str = ""
