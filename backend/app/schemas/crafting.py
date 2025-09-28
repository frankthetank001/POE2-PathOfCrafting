from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class ItemRarity(str, Enum):
    NORMAL = "Normal"
    MAGIC = "Magic"
    RARE = "Rare"
    UNIQUE = "Unique"


class ModType(str, Enum):
    PREFIX = "prefix"
    SUFFIX = "suffix"
    IMPLICIT = "implicit"
    DESECRATED = "desecrated"


class ModifierValue(BaseModel):
    text: str
    value: float
    min_value: float
    max_value: float


class ItemModifier(BaseModel):
    id: Optional[int] = None
    name: str
    mod_type: ModType
    tier: int
    stat_text: str
    stat_min: Optional[float] = None
    stat_max: Optional[float] = None
    current_value: Optional[float] = None
    required_ilvl: Optional[int] = None
    mod_group: Optional[str] = None
    applicable_items: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    is_exclusive: bool = False  # True if mod is only available on unique/special items


class CraftableItem(BaseModel):
    base_name: str
    base_category: str
    rarity: ItemRarity
    item_level: int
    quality: int = 0

    implicit_mods: List[ItemModifier] = Field(default_factory=list)
    prefix_mods: List[ItemModifier] = Field(default_factory=list)
    suffix_mods: List[ItemModifier] = Field(default_factory=list)

    corrupted: bool = False
    base_stats: Dict[str, int] = Field(default_factory=dict)  # Base stats from item base
    calculated_stats: Dict[str, int] = Field(default_factory=dict)  # Final calculated stats

    @property
    def prefix_count(self) -> int:
        return len(self.prefix_mods)

    @property
    def suffix_count(self) -> int:
        return len(self.suffix_mods)

    @property
    def total_explicit_mods(self) -> int:
        return self.prefix_count + self.suffix_count

    @property
    def max_prefixes(self) -> int:
        if self.rarity == ItemRarity.MAGIC:
            return 1
        elif self.rarity == ItemRarity.RARE:
            return 3
        return 0

    @property
    def max_suffixes(self) -> int:
        if self.rarity == ItemRarity.MAGIC:
            return 1
        elif self.rarity == ItemRarity.RARE:
            return 3
        return 0

    @property
    def can_add_prefix(self) -> bool:
        return self.prefix_count < self.max_prefixes

    @property
    def can_add_suffix(self) -> bool:
        return self.suffix_count < self.max_suffixes

    @property
    def has_open_affix(self) -> bool:
        return self.can_add_prefix or self.can_add_suffix


class CraftingStep(BaseModel):
    step_number: int
    currency_name: str
    action_description: str
    possible_outcomes: List[str]
    success_probability: Optional[float] = None
    cost_estimate: Optional[float] = None


class CraftingPlan(BaseModel):
    start_item: CraftableItem
    goal_mods: List[str]
    steps: List[CraftingStep]
    total_success_probability: float
    estimated_cost: Dict[str, float]
    alternative_strategies: List[str] = Field(default_factory=list)


class CraftingSimulationRequest(BaseModel):
    item: CraftableItem
    currency_name: str


class CraftingSimulationResult(BaseModel):
    success: bool
    result_item: Optional[CraftableItem] = None
    message: str
    probabilities: Dict[str, float] = Field(default_factory=dict)


class BaseItemInfo(BaseModel):
    id: int
    name: str
    category: str
    subcategory: Optional[str] = None
    base_stats: Dict = Field(default_factory=dict)
    required_level: int = 0
    implicit_mod: Optional[ItemModifier] = None


class ModifierInfo(BaseModel):
    id: int
    name: str
    mod_type: ModType
    tier: int
    stat_text: str
    stat_min: Optional[float] = None
    stat_max: Optional[float] = None
    required_ilvl: int = 0
    weight: int = 1000
    mod_group: Optional[str] = None
    applicable_items: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)


class CurrencyInfo(BaseModel):
    id: int
    name: str
    short_name: str
    function: str
    rarity: str
    rules: Dict = Field(default_factory=dict)