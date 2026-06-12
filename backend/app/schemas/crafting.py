from enum import Enum
from functools import cached_property
from typing import TYPE_CHECKING, Dict, FrozenSet, List, Optional

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from app.core.item_classification import ItemClassification, DefenseType


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
    RUNE = "rune"


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
    mod_id: Optional[str] = None  # String ID from pob-data (e.g., "LocalAddedPhysicalDamageTwoHand5")
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
    weight: int = 100  # Weighting for random selection
    mod_group: Optional[str] = None
    applicable_items: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    weight_conditions: Optional[Dict[str, List]] = None  # PoB2 weightKey/weightVal: {"weightKey": ["ranged", "two_hand_weapon"], "weightVal": [0, 1]}
    is_exclusive: bool = False  # True if mod is only available on unique/special items
    is_essence_only: bool = False  # True if mod is only available from essences
    is_unrevealed: bool = False  # True if this is an unrevealed desecrated modifier
    unrevealed_id: Optional[str] = None  # ID linking to UnrevealedModifier metadata
    is_desecrated: bool = False  # True if this mod was added via desecration (for green tint)
    is_fractured: bool = False  # True if this mod is fractured (cannot be removed, displayed in orange)
    is_crafted: bool = False  # True if this is the item's crafted mod (0.5: from essence/alloy; teal tint, max 1)
    exclusion_group: Optional[int] = None  # Mods in the same exclusion group cannot coexist
    trade_hash: Optional[int] = None  # Trade API stat hash for searching (from pob-data tradeHash)


class UnrevealedModifier(BaseModel):
    """Represents an unrevealed desecrated modifier that needs to be revealed by the player"""
    id: str  # Unique ID for this unrevealed mod
    mod_type: ModType  # Whether it will be a prefix or suffix
    bone_type: str  # Type of bone used (gnawed/preserved/ancient)
    bone_part: str  # Part of bone (jawbone/rib/collarbone/cranium/vertebrae)
    min_modifier_level: Optional[int] = None  # For ancient bones
    required_boss_tag: Optional[str] = None  # ulaman/amanamu/kurgal if boss omen was used
    has_abyssal_echoes: bool = False  # True if Omen of Abyssal Echoes was active


class SocketedRune(BaseModel):
    """Represents a rune socketed into an item"""
    name: str  # Display name (e.g., "Greater Iron Rune")
    base_type: str  # Base type name
    icon: Optional[str] = None  # URL to rune icon
    socket_index: int = 0  # Which socket this rune is in (0-indexed)
    mods: List[str] = Field(default_factory=list)  # Mod texts that apply to this item type
    bonded_mods: List[str] = Field(default_factory=list)  # Class-specific "Bonded" mods


class CraftableItem(BaseModel):
    base_name: str
    base_category: str
    slot: Optional[str] = None  # Equipment slot (helmet, body_armour, boots, etc.)
    rarity: ItemRarity
    item_level: int
    quality: int = 0

    implicit_mods: List[ItemModifier] = Field(default_factory=list)
    prefix_mods: List[ItemModifier] = Field(default_factory=list)
    suffix_mods: List[ItemModifier] = Field(default_factory=list)
    unrevealed_mods: List[UnrevealedModifier] = Field(default_factory=list)  # Unrevealed desecrated mods
    socketed_runes: List[SocketedRune] = Field(default_factory=list)  # Runes socketed into this item

    corrupted: bool = False
    base_stats: Dict[str, float] = Field(default_factory=dict)  # Base stats from item base (int or float)
    calculated_stats: Dict[str, float] = Field(default_factory=dict)  # Final calculated stats (int or float)

    # Catalyst quality (rings/amulets only, not belts)
    catalyst_type: Optional[str] = None  # "flesh", "neural", "carapace", etc.
    catalyst_quality: int = 0  # 0-20% (each catalyst adds 5%)

    @property
    def prefix_count(self) -> int:
        # Count all prefixes (including unrevealed placeholders)
        # Unrevealed mods are now stored as placeholders in prefix_mods with is_unrevealed=True
        return len(self.prefix_mods)

    @property
    def suffix_count(self) -> int:
        # Count all suffixes (including unrevealed placeholders)
        # Unrevealed mods are now stored as placeholders in suffix_mods with is_unrevealed=True
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

    # === Item Classification Convenience Properties ===
    # These delegate to the centralized ItemClassification system

    def _get_slot(self) -> str:
        """Get the item slot from the slot field, item base, or falling back to category."""
        if self.slot:
            return self.slot
        from app.schemas.item_bases import get_item_base_by_name
        base = get_item_base_by_name(self.base_name)
        return base.slot if base else self.base_category

    def get_classification(self) -> "ItemClassification":
        """Get the full ItemClassification for this item."""
        from app.core.item_classification import classify_item
        return classify_item(self.base_category, self._get_slot())

    @property
    def is_weapon(self) -> bool:
        """Check if this is any type of weapon."""
        return self.get_classification().is_weapon

    @property
    def is_armor(self) -> bool:
        """Check if this is an armor piece (body, helmet, gloves, boots)."""
        return self.get_classification().is_armor

    @property
    def is_jewelry(self) -> bool:
        """Check if this is jewelry (ring, amulet, belt)."""
        return self.get_classification().is_jewelry

    @property
    def is_accessory(self) -> bool:
        """Alias for is_jewelry."""
        return self.is_jewelry

    @property
    def is_offhand(self) -> bool:
        """Check if this is an offhand item (shield, quiver, focus)."""
        return self.get_classification().is_offhand

    @property
    def is_shield(self) -> bool:
        """Check if this is a shield."""
        return self.get_classification().is_shield

    @property
    def is_one_handed(self) -> bool:
        """Check if this is a one-handed weapon."""
        return self.get_classification().is_one_handed

    @property
    def is_two_handed(self) -> bool:
        """Check if this is a two-handed weapon."""
        return self.get_classification().is_two_handed

    @property
    def is_caster_weapon(self) -> bool:
        """Check if this is a caster weapon (staff, wand, sceptre)."""
        return self.get_classification().is_caster_weapon

    @property
    def is_attack_weapon(self) -> bool:
        """Check if this is an attack weapon (non-caster)."""
        return self.get_classification().is_attack_weapon

    @property
    def is_melee_weapon(self) -> bool:
        """Check if this is a melee weapon."""
        return self.get_classification().is_melee_weapon

    @property
    def is_ranged_weapon(self) -> bool:
        """Check if this is a ranged weapon (bow, crossbow)."""
        return self.get_classification().is_ranged_weapon

    @property
    def defense_types(self) -> FrozenSet["DefenseType"]:
        """Get the defense types for this armor piece."""
        return self.get_classification().defense_types

    @property
    def has_armour_defense(self) -> bool:
        """Check if this armor has Armour defense."""
        return self.get_classification().has_armour

    @property
    def has_evasion_defense(self) -> bool:
        """Check if this armor has Evasion defense."""
        return self.get_classification().has_evasion

    @property
    def has_energy_shield_defense(self) -> bool:
        """Check if this armor has Energy Shield defense."""
        return self.get_classification().has_energy_shield


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
    mod_id: Optional[str] = None  # Direct reference to mod ID in ModItem.json


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