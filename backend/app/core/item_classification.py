"""
Item Classification System - Single source of truth for item type checks.

This module provides centralized enums, constants, and utilities for determining
item properties like is_weapon, is_caster, is_one_handed, etc.

Usage:
    # Standalone utility - works with any category/slot strings
    classification = classify_item(category="sword", slot="weapons - 1 hand")
    if classification.is_caster_weapon:
        ...

    # Or use the convenience properties on CraftableItem
    if item.is_caster_weapon:
        ...
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set


# =============================================================================
# ENUMS - Type-safe item classifications
# =============================================================================

class ItemSlot(str, Enum):
    """Equipment slot where an item is worn/wielded."""
    BODY_ARMOUR = "body_armour"
    HELMET = "helmet"
    GLOVES = "gloves"
    BOOTS = "boots"
    WEAPONS_1H = "weapons - 1 hand"
    WEAPONS_2H = "weapons - 2 hand"
    OFFHAND = "offhand"
    SHIELD = "shield"
    RING = "ring"
    AMULET = "amulet"
    BELT = "belt"
    TALISMAN = "talisman"
    JEWEL = "jewel"
    QUIVER = "quiver"
    FOCUS = "focus"

    @classmethod
    def armor_slots(cls) -> FrozenSet["ItemSlot"]:
        """Get all armor equipment slots."""
        return frozenset({cls.BODY_ARMOUR, cls.HELMET, cls.GLOVES, cls.BOOTS})

    @classmethod
    def weapon_slots(cls) -> FrozenSet["ItemSlot"]:
        """Get all weapon slots."""
        return frozenset({cls.WEAPONS_1H, cls.WEAPONS_2H})

    @classmethod
    def jewelry_slots(cls) -> FrozenSet["ItemSlot"]:
        """Get all jewelry/accessory slots."""
        return frozenset({cls.RING, cls.AMULET, cls.BELT})

    @classmethod
    def offhand_slots(cls) -> FrozenSet["ItemSlot"]:
        """Get all offhand slots."""
        return frozenset({cls.OFFHAND, cls.SHIELD, cls.QUIVER, cls.FOCUS})


class WeaponCategory(str, Enum):
    """Specific weapon types."""
    SWORD = "sword"
    AXE = "axe"
    MACE = "mace"
    BOW = "bow"
    CROSSBOW = "crossbow"
    STAFF = "staff"
    WARSTAFF = "warstaff"
    WAND = "wand"
    DAGGER = "dagger"
    CLAW = "claw"
    SCEPTRE = "sceptre"
    FLAIL = "flail"
    SPEAR = "spear"


class ArmorCategory(str, Enum):
    """Armor attribute types (determines which defense types are present)."""
    STR_ARMOUR = "str_armour"
    DEX_ARMOUR = "dex_armour"
    INT_ARMOUR = "int_armour"
    STR_DEX_ARMOUR = "str_dex_armour"
    STR_INT_ARMOUR = "str_int_armour"
    DEX_INT_ARMOUR = "dex_int_armour"
    STR_DEX_INT_ARMOUR = "str_dex_int_armour"


class DefenseType(str, Enum):
    """Defense stat types for armor."""
    ARMOUR = "armour"
    EVASION = "evasion"
    ENERGY_SHIELD = "energy_shield"


class OffhandCategory(str, Enum):
    """Offhand equipment types."""
    SHIELD = "shield"
    QUIVER = "quiver"
    FOCUS = "focus"


class ShieldCategory(str, Enum):
    """Shield subtypes by attribute requirement."""
    STR_SHIELD = "str_shield"
    DEX_SHIELD = "dex_shield"
    INT_SHIELD = "int_shield"
    STR_DEX_SHIELD = "str_dex_shield"
    STR_INT_SHIELD = "str_int_shield"
    DEX_INT_SHIELD = "dex_int_shield"
    BUCKLER = "buckler"


class AccessoryCategory(str, Enum):
    """Jewelry/accessory types."""
    RING = "ring"
    AMULET = "amulet"
    BELT = "belt"


class WeaponClass(str, Enum):
    """Broad weapon classification."""
    MELEE = "melee"
    RANGED = "ranged"
    CASTER = "caster"


# =============================================================================
# FROZEN SETS - Single source of truth for category groupings
# =============================================================================

# Weapons that can be one-handed
ONE_HANDED_WEAPONS: FrozenSet[str] = frozenset({
    WeaponCategory.SWORD.value,
    WeaponCategory.AXE.value,
    WeaponCategory.MACE.value,
    WeaponCategory.DAGGER.value,
    WeaponCategory.CLAW.value,
    WeaponCategory.WAND.value,
    WeaponCategory.SCEPTRE.value,
    WeaponCategory.FLAIL.value,
})

# Weapons that can be two-handed
TWO_HANDED_WEAPONS: FrozenSet[str] = frozenset({
    WeaponCategory.SWORD.value,
    WeaponCategory.AXE.value,
    WeaponCategory.MACE.value,
    WeaponCategory.BOW.value,
    WeaponCategory.CROSSBOW.value,
    WeaponCategory.STAFF.value,
    WeaponCategory.WARSTAFF.value,
    WeaponCategory.SPEAR.value,
})

# Caster weapons (spell-focused)
CASTER_WEAPONS: FrozenSet[str] = frozenset({
    WeaponCategory.STAFF.value,
    WeaponCategory.WAND.value,
    WeaponCategory.SCEPTRE.value,
})

# Attack weapons (non-caster, used with "weapon" weight key)
ATTACK_WEAPONS: FrozenSet[str] = frozenset({
    WeaponCategory.SWORD.value,
    WeaponCategory.AXE.value,
    WeaponCategory.MACE.value,
    WeaponCategory.BOW.value,
    WeaponCategory.CROSSBOW.value,
    WeaponCategory.DAGGER.value,
    WeaponCategory.CLAW.value,
    WeaponCategory.FLAIL.value,
    WeaponCategory.SPEAR.value,
    WeaponCategory.WARSTAFF.value,
})

# Ranged weapons
RANGED_WEAPONS: FrozenSet[str] = frozenset({
    WeaponCategory.BOW.value,
    WeaponCategory.CROSSBOW.value,
})

# Melee weapons
MELEE_WEAPONS: FrozenSet[str] = frozenset({
    WeaponCategory.SWORD.value,
    WeaponCategory.AXE.value,
    WeaponCategory.MACE.value,
    WeaponCategory.DAGGER.value,
    WeaponCategory.CLAW.value,
    WeaponCategory.FLAIL.value,
    WeaponCategory.SPEAR.value,
    WeaponCategory.WARSTAFF.value,
})

# All weapon categories
ALL_WEAPON_CATEGORIES: FrozenSet[str] = frozenset({w.value for w in WeaponCategory})

# All armor attribute categories
ALL_ARMOR_CATEGORIES: FrozenSet[str] = frozenset({a.value for a in ArmorCategory})

# Jewelry categories
JEWELRY_CATEGORIES: FrozenSet[str] = frozenset({
    AccessoryCategory.RING.value,
    AccessoryCategory.AMULET.value,
    AccessoryCategory.BELT.value,
})

# Offhand categories
OFFHAND_CATEGORIES: FrozenSet[str] = frozenset({
    OffhandCategory.SHIELD.value,
    OffhandCategory.QUIVER.value,
    OffhandCategory.FOCUS.value,
})

# Shield categories
ALL_SHIELD_CATEGORIES: FrozenSet[str] = frozenset({s.value for s in ShieldCategory})


# =============================================================================
# MAPPING DICTIONARIES
# =============================================================================

# Armor category to defense types
ARMOR_CATEGORY_TO_DEFENSES: Dict[str, FrozenSet[DefenseType]] = {
    ArmorCategory.STR_ARMOUR.value: frozenset({DefenseType.ARMOUR}),
    ArmorCategory.DEX_ARMOUR.value: frozenset({DefenseType.EVASION}),
    ArmorCategory.INT_ARMOUR.value: frozenset({DefenseType.ENERGY_SHIELD}),
    ArmorCategory.STR_DEX_ARMOUR.value: frozenset({DefenseType.ARMOUR, DefenseType.EVASION}),
    ArmorCategory.STR_INT_ARMOUR.value: frozenset({DefenseType.ARMOUR, DefenseType.ENERGY_SHIELD}),
    ArmorCategory.DEX_INT_ARMOUR.value: frozenset({DefenseType.EVASION, DefenseType.ENERGY_SHIELD}),
    ArmorCategory.STR_DEX_INT_ARMOUR.value: frozenset({
        DefenseType.ARMOUR, DefenseType.EVASION, DefenseType.ENERGY_SHIELD
    }),
}

# Defense mod patterns by armor category (for filtering applicable mods)
ARMOR_DEFENSE_PATTERNS: Dict[str, List[str]] = {
    ArmorCategory.STR_ARMOUR.value: ["% increased Armour"],
    ArmorCategory.DEX_ARMOUR.value: ["% increased Evasion"],
    ArmorCategory.INT_ARMOUR.value: ["% increased Energy Shield"],
    ArmorCategory.STR_DEX_ARMOUR.value: ["% increased Armour and Evasion"],
    ArmorCategory.STR_INT_ARMOUR.value: ["% increased Armour and Energy Shield"],
    ArmorCategory.DEX_INT_ARMOUR.value: ["% increased Evasion and Energy Shield"],
    ArmorCategory.STR_DEX_INT_ARMOUR.value: [
        "% increased Armour",
        "% increased Evasion",
        "% increased Energy Shield",
        "% increased Armour and Evasion",
        "% increased Armour and Energy Shield",
        "% increased Evasion and Energy Shield",
    ],
}

# POB name format -> database category format
POB_TO_DB_CATEGORY: Dict[str, str] = {
    "One Handed Axe": "axe",
    "One Handed Mace": "mace",
    "One Handed Sword": "sword",
    "Two Handed Axe": "axe",
    "Two Handed Mace": "mace",
    "Two Handed Sword": "sword",
    "Wand": "wand",
    "Dagger": "dagger",
    "Spear": "spear",
    "Sceptre": "sceptre",
    "Flail": "flail",
    "Claw": "claw",
    "Bow": "bow",
    "Crossbow": "crossbow",
    "Staff": "staff",
    "Warstaff": "warstaff",
    "Body Armour": "body_armour",
    "Helmet": "helmet",
    "Gloves": "gloves",
    "Boots": "boots",
    "Shield": "shield",
    "Quiver": "quiver",
    "Amulet": "amulet",
    "Ring": "ring",
    "Belt": "belt",
}

# Category to Trade API format
CATEGORY_TO_TRADE_API: Dict[str, str] = {
    # Armour slots
    "boots": "armour.boots",
    "gloves": "armour.gloves",
    "helmet": "armour.helmet",
    "body_armour": "armour.chest",
    "body": "armour.chest",  # Alias
    "shield": "armour.shield",
    "quiver": "armour.quiver",
    "focus": "armour.focus",
    # Accessories
    "ring": "accessory.ring",
    "amulet": "accessory.amulet",
    "belt": "accessory.belt",
    # Weapons
    "wand": "weapon.wand",
    "staff": "weapon.staff",
    "warstaff": "weapon.warstaff",
    "bow": "weapon.bow",
    "crossbow": "weapon.crossbow",
    "mace": "weapon.mace",
    "sceptre": "weapon.sceptre",
    "sword": "weapon.sword",
    "axe": "weapon.axe",
    "dagger": "weapon.dagger",
    "claw": "weapon.claw",
    "flail": "weapon.flail",
    "spear": "weapon.spear",
    "talisman": "weapon.talisman",
}

# UI display name -> database name (for slot/category normalization)
UI_TO_DB_SLOT: Dict[str, str] = {
    "body": "body_armour",
    "weapon - 1 hand": "weapons - 1 hand",
    "weapon - 2 hand": "weapons - 2 hand",
    "1h weapon": "weapons - 1 hand",
    "2h weapon": "weapons - 2 hand",
    "quarterstaff": "warstaff",
}

# Slot to applicable categories mapping
SLOT_TO_CATEGORIES: Dict[str, FrozenSet[str]] = {
    ItemSlot.BODY_ARMOUR.value: ALL_ARMOR_CATEGORIES,
    ItemSlot.HELMET.value: ALL_ARMOR_CATEGORIES,
    ItemSlot.GLOVES.value: ALL_ARMOR_CATEGORIES,
    ItemSlot.BOOTS.value: ALL_ARMOR_CATEGORIES,
    ItemSlot.WEAPONS_1H.value: ONE_HANDED_WEAPONS,
    ItemSlot.WEAPONS_2H.value: TWO_HANDED_WEAPONS,
    ItemSlot.SHIELD.value: ALL_SHIELD_CATEGORIES | {"shield"},
    ItemSlot.QUIVER.value: frozenset({"quiver"}),
    ItemSlot.FOCUS.value: frozenset({"focus"}),
    ItemSlot.RING.value: frozenset({"ring"}),
    ItemSlot.AMULET.value: frozenset({"amulet"}),
    ItemSlot.BELT.value: frozenset({"belt"}),
    ItemSlot.TALISMAN.value: frozenset({"talisman"}),
    ItemSlot.JEWEL.value: frozenset({"jewel"}),
}


def _build_essence_item_type_mapping() -> Dict[str, List[str]]:
    """Build the essence item type to category mapping using centralized constants."""
    all_armor_list = list(ALL_ARMOR_CATEGORIES)
    body_armor_list = ["body_armour"] + all_armor_list

    return {
        # Armour types
        "Armour": body_armor_list + ["helmet", "gloves", "boots", "shield"],
        "Body Armour": body_armor_list,
        "Helmet": ["helmet"],
        "Gloves": ["gloves"],
        "Boots": ["boots"],
        "Shield": ["shield"],
        # Jewellery
        "Jewellery": ["amulet", "ring"],
        "Amulet": ["amulet"],
        "Ring": ["ring"],
        "Belt": ["belt"],
        # Weapons - using centralized weapon lists where possible
        "One Handed Melee Weapon": ["sword", "dagger", "claw", "mace", "axe", "sceptre", "wand", "flail"],
        "Two Handed Melee Weapon": ["sword", "staff", "warstaff", "flail", "spear", "talisman", "mace", "axe"],
        "Bow": ["bow"],
        "Crossbow": ["crossbow"],
        "Martial Weapon": list(ATTACK_WEAPONS) + ["talisman"],
        "Caster Weapon": list(CASTER_WEAPONS),
        "Quarterstaff": ["staff", "warstaff"],
        "Focus": ["focus"],
        # Generic
        "Equipment": body_armor_list + ["helmet", "gloves", "boots", "shield", "amulet", "ring", "belt"],
    }


# Essence item type to category mapping (used for essence effect applicability)
ESSENCE_ITEM_TYPE_TO_CATEGORY: Dict[str, List[str]] = _build_essence_item_type_mapping()


# =============================================================================
# ITEM CLASSIFICATION DATACLASS
# =============================================================================

@dataclass
class ItemClassification:
    """
    Rich item classification with computed properties.

    This class provides a single source of truth for determining
    item properties based on category and slot.

    Example:
        classification = classify_item("sword", "weapons - 1 hand")
        if classification.is_one_handed:
            ...
        if classification.is_melee_weapon:
            ...
    """
    category: str
    slot: str
    tags: List[str] = field(default_factory=list)

    # === Type checks ===

    @property
    def is_weapon(self) -> bool:
        """Check if this is any type of weapon."""
        return (
            self.category in ALL_WEAPON_CATEGORIES
            or self.slot in (ItemSlot.WEAPONS_1H.value, ItemSlot.WEAPONS_2H.value)
        )

    @property
    def is_armor(self) -> bool:
        """Check if this is an armor piece (body, helmet, gloves, boots)."""
        return (
            self.category in ALL_ARMOR_CATEGORIES
            or self.slot in (
                ItemSlot.BODY_ARMOUR.value,
                ItemSlot.HELMET.value,
                ItemSlot.GLOVES.value,
                ItemSlot.BOOTS.value,
            )
        )

    @property
    def is_armor_slot(self) -> bool:
        """Check if this item goes in an armor slot."""
        return self.slot in (
            ItemSlot.BODY_ARMOUR.value,
            ItemSlot.HELMET.value,
            ItemSlot.GLOVES.value,
            ItemSlot.BOOTS.value,
        )

    @property
    def is_accessory(self) -> bool:
        """Check if this is jewelry/accessory (ring, amulet, belt)."""
        return self.category in JEWELRY_CATEGORIES or self.slot in JEWELRY_CATEGORIES

    @property
    def is_jewelry(self) -> bool:
        """Alias for is_accessory."""
        return self.is_accessory

    @property
    def is_offhand(self) -> bool:
        """Check if this is an offhand item (shield, quiver, focus)."""
        return (
            self.category in OFFHAND_CATEGORIES
            or self.slot in (ItemSlot.OFFHAND.value, ItemSlot.SHIELD.value,
                            ItemSlot.QUIVER.value, ItemSlot.FOCUS.value)
        )

    @property
    def is_shield(self) -> bool:
        """Check if this is a shield."""
        return (
            self.category == OffhandCategory.SHIELD.value
            or self.category in ALL_SHIELD_CATEGORIES
            or self.slot == ItemSlot.SHIELD.value
            or "shield" in self.category
        )

    # === Weapon-specific properties ===

    @property
    def is_one_handed(self) -> bool:
        """Check if this is a one-handed weapon."""
        if not self.is_weapon:
            return False
        # Slot takes precedence (most reliable indicator)
        if self.slot == ItemSlot.WEAPONS_1H.value:
            return True
        if self.slot == ItemSlot.WEAPONS_2H.value:
            return False
        # Check tags next
        tags_str = " ".join(self.tags)
        if "one_hand" in tags_str or "onehand" in tags_str:
            return True
        if "two_hand" in tags_str or "twohand" in tags_str:
            return False
        # Fall back to category (some weapons like bow/crossbow are always 2h)
        if self.category in RANGED_WEAPONS:
            return False  # Bows/crossbows are always 2h
        return self.category in ONE_HANDED_WEAPONS

    @property
    def is_two_handed(self) -> bool:
        """Check if this is a two-handed weapon."""
        if not self.is_weapon:
            return False
        # Slot takes precedence (most reliable indicator)
        if self.slot == ItemSlot.WEAPONS_2H.value:
            return True
        if self.slot == ItemSlot.WEAPONS_1H.value:
            return False
        # Check tags next
        tags_str = " ".join(self.tags)
        if "two_hand" in tags_str or "twohand" in tags_str:
            return True
        if "one_hand" in tags_str or "onehand" in tags_str:
            return False
        # Fall back to category (some weapons like bow/crossbow are always 2h)
        if self.category in RANGED_WEAPONS:
            return True  # Bows/crossbows are always 2h
        return self.category in TWO_HANDED_WEAPONS and self.category not in ONE_HANDED_WEAPONS

    @property
    def is_caster_weapon(self) -> bool:
        """Check if this is a caster weapon (staff, wand, sceptre)."""
        return self.category in CASTER_WEAPONS

    @property
    def is_attack_weapon(self) -> bool:
        """Check if this is an attack weapon (non-caster)."""
        return self.is_weapon and self.category in ATTACK_WEAPONS

    @property
    def is_melee_weapon(self) -> bool:
        """Check if this is a melee weapon."""
        return self.category in MELEE_WEAPONS

    @property
    def is_ranged_weapon(self) -> bool:
        """Check if this is a ranged weapon (bow, crossbow)."""
        return self.category in RANGED_WEAPONS

    @property
    def weapon_class(self) -> Optional[WeaponClass]:
        """Get the broad weapon classification."""
        if not self.is_weapon:
            return None
        if self.is_caster_weapon:
            return WeaponClass.CASTER
        if self.is_ranged_weapon:
            return WeaponClass.RANGED
        return WeaponClass.MELEE

    # === Armor-specific properties ===

    @property
    def defense_types(self) -> FrozenSet[DefenseType]:
        """Get the defense types for this armor piece."""
        return ARMOR_CATEGORY_TO_DEFENSES.get(self.category, frozenset())

    @property
    def has_armour(self) -> bool:
        """Check if this armor has Armour defense."""
        return DefenseType.ARMOUR in self.defense_types

    @property
    def has_evasion(self) -> bool:
        """Check if this armor has Evasion defense."""
        return DefenseType.EVASION in self.defense_types

    @property
    def has_energy_shield(self) -> bool:
        """Check if this armor has Energy Shield defense."""
        return DefenseType.ENERGY_SHIELD in self.defense_types

    # === Helper methods ===

    def matches_weight_key(self, weight_key: str) -> bool:
        """
        Check if this item matches a PoB weight key.

        This is used for determining mod applicability based on the
        weightKey/weightVal system from PoB data.

        Args:
            weight_key: The weight key to check (e.g., "ranged", "two_hand_weapon", "bow")

        Returns:
            True if this item matches the weight key
        """
        # Direct category match (bow, sword, str_armour, etc.)
        if weight_key == self.category:
            return True

        # Direct slot match
        if weight_key == self.slot:
            return True

        # Check if weight_key matches any of the item's tags
        # Critical for armor defense types (e.g., dex_int_armour on a helmet)
        if weight_key in self.tags:
            return True

        # === Generic weapon tags ===

        # "ranged" - bow, crossbow only
        if weight_key == "ranged" and self.is_ranged_weapon:
            return True

        # "one_hand_weapon" - attack weapons only (excludes caster)
        if weight_key == "one_hand_weapon":
            if self.is_one_handed and not self.is_caster_weapon:
                return True

        # "two_hand_weapon" - attack weapons only (excludes staff)
        if weight_key == "two_hand_weapon":
            if self.is_two_handed and self.category != "staff":
                return True

        # "weapon" - attack weapons only (excludes caster weapons)
        if weight_key == "weapon":
            if self.is_weapon and not self.is_caster_weapon:
                return True

        # === Generic armor tags ===

        # "armour" - any armor category
        if weight_key == "armour" and "armour" in self.category:
            return True

        # === Jewelry ===
        if weight_key == "jewellery" and self.is_jewelry:
            return True

        # === Shield sub-types ===
        if "shield" in weight_key and self.is_shield:
            if weight_key == "shield":
                return True
            if weight_key == self.category:
                return True

        # === Default always matches ===
        if weight_key == "default":
            return True

        return False

    def get_applicable_defense_patterns(self) -> List[str]:
        """Get the defense mod patterns applicable to this armor."""
        return ARMOR_DEFENSE_PATTERNS.get(self.category, [])

    def get_trade_category(self) -> Optional[str]:
        """Get the trade API category for this item."""
        # For weapons, use category; for armor slots, use slot
        if self.is_weapon:
            return CATEGORY_TO_TRADE_API.get(self.category)
        if self.is_armor_slot:
            return CATEGORY_TO_TRADE_API.get(self.slot)
        # For jewelry and other, use category
        return CATEGORY_TO_TRADE_API.get(self.category) or CATEGORY_TO_TRADE_API.get(self.slot)


# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def classify_item(
    category: str,
    slot: str,
    tags: Optional[List[str]] = None
) -> ItemClassification:
    """
    Create an ItemClassification from category and slot strings.

    This is the main entry point for classifying items.

    Args:
        category: The item's category (e.g., "sword", "str_armour", "ring")
        slot: The item's slot (e.g., "weapons - 1 hand", "body_armour", "ring")
        tags: Optional list of tags from the item base

    Returns:
        ItemClassification with computed properties

    Example:
        classification = classify_item("sword", "weapons - 1 hand")
        if classification.is_melee_weapon:
            ...
    """
    return ItemClassification(
        category=category,
        slot=slot,
        tags=tags or []
    )


def normalize_slot(slot: str) -> str:
    """
    Normalize a slot name to the database format.

    Args:
        slot: The slot name (may be UI format or database format)

    Returns:
        Normalized slot name in database format
    """
    return UI_TO_DB_SLOT.get(slot.lower(), slot)


def normalize_category(category: str) -> str:
    """
    Normalize a category name to the database format.

    Args:
        category: The category name (may be POB format or database format)

    Returns:
        Normalized category name in database format
    """
    return POB_TO_DB_CATEGORY.get(category, category.lower())


def is_valid_weapon_category(category: str) -> bool:
    """Check if a category string is a valid weapon category."""
    return category in ALL_WEAPON_CATEGORIES


def is_valid_armor_category(category: str) -> bool:
    """Check if a category string is a valid armor category."""
    return category in ALL_ARMOR_CATEGORIES


def is_valid_jewelry_category(category: str) -> bool:
    """Check if a category string is a valid jewelry category."""
    return category in JEWELRY_CATEGORIES


def get_categories_for_slot(slot: str) -> FrozenSet[str]:
    """Get all valid categories for a given slot."""
    return SLOT_TO_CATEGORIES.get(slot, frozenset())


# =============================================================================
# HELPER FUNCTIONS FOR MOD APPLICABILITY
# =============================================================================

def is_defense_mod_applicable(mod_stat_text: str, category: str) -> bool:
    """
    Check if a defense % mod is applicable to an armor piece.

    E.g., "% increased Armour" only applies to str_armour items.

    Args:
        mod_stat_text: The mod's stat text
        category: The armor category

    Returns:
        True if the mod is applicable, False otherwise
    """
    if category not in ALL_ARMOR_CATEGORIES:
        return True  # Not an armor, defense check not applicable

    patterns = ARMOR_DEFENSE_PATTERNS.get(category, [])
    if not patterns:
        return True

    # Check if mod matches any applicable pattern
    for pattern in patterns:
        if pattern in mod_stat_text:
            return True

    # If it's a defense mod but doesn't match, reject it
    defense_keywords = ["% increased Armour", "% increased Evasion", "% increased Energy Shield"]
    if any(kw in mod_stat_text for kw in defense_keywords):
        return False

    return True
