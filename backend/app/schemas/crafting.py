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


class StatRange(BaseModel):
    min: float
    max: float


class ItemModifier(BaseModel):
    id: Optional[int] = None
    name: str
    mod_type: ModType
    tier: int
    stat_text: str
    stat_ranges: List[StatRange] = Field(default_factory=list)  # Multiple ranges for hybrid mods
    stat_min: Optional[float] = None  # Legacy: first range min
    stat_max: Optional[float] = None  # Legacy: first range max
    current_value: Optional[float] = None  # Legacy: first value
    current_values: Optional[List[float]] = None  # All rolled values for multi-stat mods
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


class CraftingSimulationWithOmensRequest(BaseModel):
    item: CraftableItem
    currency_name: str
    omen_names: List[str] = Field(default_factory=list)


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


class EssenceItemEffect(BaseModel):
    id: int
    essence_id: int
    item_type: str  # "Belt", "Body Armour", "Amulet", etc.
    modifier_type: str  # prefix, suffix
    effect_text: str  # "+(30-39) to maximum Life"
    value_min: Optional[float] = None  # 30
    value_max: Optional[float] = None  # 39


class EssenceInfo(BaseModel):
    id: int
    name: str
    essence_tier: str  # lesser, normal, greater, perfect, corrupted
    essence_type: str  # body, mind, enhancement, etc.
    mechanic: str  # magic_to_rare, remove_add_rare
    stack_size: int = 10
    item_effects: List[EssenceItemEffect] = Field(default_factory=list)


class OmenRule(BaseModel):
    id: int
    omen_id: int
    rule_type: str  # "force_prefix", "force_suffix", "add_two", etc.
    rule_value: Optional[str] = None  # Additional rule parameters
    priority: int = 0  # Rule application order


class OmenInfo(BaseModel):
    id: int
    name: str
    effect_description: str
    affected_currency: str  # "Chaos Orb", "Exalted Orb", etc.
    effect_type: str  # "sinistral", "dextral", "greater", etc.
    stack_size: int = 10
    rules: List[OmenRule] = Field(default_factory=list)


class DesecrationBoneInfo(BaseModel):
    id: int
    name: str
    bone_type: str  # "gnawed", "preserved", "ancient"
    bone_part: str  # "jawbone", "rib", "collarbone", "cranium", "vertebrae"
    mechanic: str  # "add_desecrated_mod"
    stack_size: int = 20
    applicable_items: List[str] = Field(default_factory=list)  # ["weapon", "quiver", "armour", etc.]
    min_modifier_level: Optional[int] = None  # For ancient bones
    max_item_level: Optional[int] = None  # For gnawed bones
    function_description: Optional[str] = None


class PoolModifier(BaseModel):
    id: int
    pool_id: int
    modifier_id: int
    weight_multiplier: float = 1.0


class ModifierPoolInfo(BaseModel):
    id: int
    name: str
    pool_type: str  # "regular", "essence_only", "desecrated", "corrupted"
    description: Optional[str] = None
    modifiers: List[PoolModifier] = Field(default_factory=list)


class CurrencyConfigInfo(BaseModel):
    id: int
    name: str
    currency_type: str  # "transmutation", "essence", "omen", etc.
    tier: Optional[str] = None  # "lesser", "greater", "perfect", null for basic
    rarity: str
    stack_size: int = 20
    mechanic_class: str  # Python class name for the mechanic
    config_data: Dict = Field(default_factory=dict)  # Currency-specific parameters