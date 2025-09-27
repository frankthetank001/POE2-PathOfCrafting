from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class League(BaseModel):
    name: str
    url: str
    display_name: str = Field(..., alias="displayName")
    hardcore: bool
    indexed: bool


class LeaguesResponse(BaseModel):
    economy_leagues: List[League] = Field(..., alias="economyLeagues")
    old_economy_leagues: List[League] = Field(default_factory=list, alias="oldEconomyLeagues")
    build_leagues: List[League] = Field(..., alias="buildLeagues")
    old_build_leagues: List[League] = Field(default_factory=list, alias="oldBuildLeagues")


class BuildCharacter(BaseModel):
    name: str
    level: int
    class_name: str = Field(..., alias="class")
    ascendancy: Optional[str] = None


class BuildItem(BaseModel):
    name: str
    type_line: str
    base_type: str
    rarity: str
    item_level: Optional[int] = None
    icon: Optional[str] = None


class BuildStats(BaseModel):
    life: Optional[int] = None
    energy_shield: Optional[int] = None
    mana: Optional[int] = None
    dps: Optional[float] = None


class Build(BaseModel):
    character: BuildCharacter
    items: Dict[str, BuildItem] = Field(default_factory=dict)
    stats: Optional[BuildStats] = None
    main_skill: Optional[str] = None


class BuildsQueryParams(BaseModel):
    league: str = Field(default="Standard")
    class_name: Optional[str] = Field(default=None, alias="class")
    min_level: Optional[int] = Field(default=None, ge=1, le=100)
    limit: int = Field(default=50, ge=1, le=100)


class BuildsResponse(BaseModel):
    builds: List[Build]
    total: int
    league: str