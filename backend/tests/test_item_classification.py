"""
Unit tests for the centralized item classification system.

Tests the enums, frozen sets, ItemClassification dataclass, and helper functions.
"""

import pytest
from app.core.item_classification import (
    # Enums
    ItemSlot,
    WeaponCategory,
    ArmorCategory,
    DefenseType,
    OffhandCategory,
    ShieldCategory,
    AccessoryCategory,
    WeaponClass,
    # Frozen sets
    ONE_HANDED_WEAPONS,
    TWO_HANDED_WEAPONS,
    CASTER_WEAPONS,
    ATTACK_WEAPONS,
    RANGED_WEAPONS,
    MELEE_WEAPONS,
    ALL_WEAPON_CATEGORIES,
    ALL_ARMOR_CATEGORIES,
    JEWELRY_CATEGORIES,
    OFFHAND_CATEGORIES,
    # Mappings
    ARMOR_CATEGORY_TO_DEFENSES,
    ARMOR_DEFENSE_PATTERNS,
    POB_TO_DB_CATEGORY,
    CATEGORY_TO_TRADE_API,
    SLOT_TO_CATEGORIES,
    # Dataclass and functions
    ItemClassification,
    classify_item,
    normalize_slot,
    normalize_category,
    is_valid_weapon_category,
    is_valid_armor_category,
    is_valid_jewelry_category,
    get_categories_for_slot,
    is_defense_mod_applicable,
)


class TestEnums:
    """Test that all enums have expected values."""

    def test_item_slot_values(self):
        """Test ItemSlot enum has expected values."""
        assert ItemSlot.BODY_ARMOUR.value == "body_armour"
        assert ItemSlot.WEAPONS_1H.value == "weapons - 1 hand"
        assert ItemSlot.WEAPONS_2H.value == "weapons - 2 hand"
        assert ItemSlot.RING.value == "ring"

    def test_weapon_category_values(self):
        """Test WeaponCategory enum has expected values."""
        assert WeaponCategory.SWORD.value == "sword"
        assert WeaponCategory.BOW.value == "bow"
        assert WeaponCategory.STAFF.value == "staff"

    def test_armor_category_values(self):
        """Test ArmorCategory enum has expected values."""
        assert ArmorCategory.STR_ARMOUR.value == "str_armour"
        assert ArmorCategory.DEX_ARMOUR.value == "dex_armour"
        assert ArmorCategory.STR_DEX_ARMOUR.value == "str_dex_armour"

    def test_defense_type_values(self):
        """Test DefenseType enum has expected values."""
        assert DefenseType.ARMOUR.value == "armour"
        assert DefenseType.EVASION.value == "evasion"
        assert DefenseType.ENERGY_SHIELD.value == "energy_shield"

    def test_item_slot_class_methods(self):
        """Test ItemSlot class methods return correct frozen sets."""
        armor_slots = ItemSlot.armor_slots()
        assert ItemSlot.BODY_ARMOUR in armor_slots
        assert ItemSlot.HELMET in armor_slots
        assert ItemSlot.WEAPONS_1H not in armor_slots

        weapon_slots = ItemSlot.weapon_slots()
        assert ItemSlot.WEAPONS_1H in weapon_slots
        assert ItemSlot.WEAPONS_2H in weapon_slots

        jewelry_slots = ItemSlot.jewelry_slots()
        assert ItemSlot.RING in jewelry_slots
        assert ItemSlot.AMULET in jewelry_slots
        assert ItemSlot.BELT in jewelry_slots


class TestFrozenSets:
    """Test that frozen sets contain expected values."""

    def test_one_handed_weapons(self):
        """Test ONE_HANDED_WEAPONS contains expected values."""
        assert "sword" in ONE_HANDED_WEAPONS
        assert "axe" in ONE_HANDED_WEAPONS
        assert "wand" in ONE_HANDED_WEAPONS
        assert "bow" not in ONE_HANDED_WEAPONS  # bow is 2h

    def test_two_handed_weapons(self):
        """Test TWO_HANDED_WEAPONS contains expected values."""
        assert "bow" in TWO_HANDED_WEAPONS
        assert "staff" in TWO_HANDED_WEAPONS
        assert "crossbow" in TWO_HANDED_WEAPONS

    def test_caster_weapons(self):
        """Test CASTER_WEAPONS contains expected values."""
        assert "staff" in CASTER_WEAPONS
        assert "wand" in CASTER_WEAPONS
        assert "sceptre" in CASTER_WEAPONS
        assert "sword" not in CASTER_WEAPONS

    def test_ranged_weapons(self):
        """Test RANGED_WEAPONS contains expected values."""
        assert "bow" in RANGED_WEAPONS
        assert "crossbow" in RANGED_WEAPONS
        assert len(RANGED_WEAPONS) == 2

    def test_jewelry_categories(self):
        """Test JEWELRY_CATEGORIES contains expected values."""
        assert "ring" in JEWELRY_CATEGORIES
        assert "amulet" in JEWELRY_CATEGORIES
        assert "belt" in JEWELRY_CATEGORIES
        assert len(JEWELRY_CATEGORIES) == 3

    def test_all_weapon_categories_complete(self):
        """Test ALL_WEAPON_CATEGORIES contains all weapon types."""
        for weapon in WeaponCategory:
            assert weapon.value in ALL_WEAPON_CATEGORIES

    def test_all_armor_categories_complete(self):
        """Test ALL_ARMOR_CATEGORIES contains all armor types."""
        for armor in ArmorCategory:
            assert armor.value in ALL_ARMOR_CATEGORIES


class TestMappings:
    """Test mapping dictionaries."""

    def test_armor_category_to_defenses(self):
        """Test armor categories map to correct defense types."""
        # Pure types
        assert ARMOR_CATEGORY_TO_DEFENSES["str_armour"] == frozenset({DefenseType.ARMOUR})
        assert ARMOR_CATEGORY_TO_DEFENSES["dex_armour"] == frozenset({DefenseType.EVASION})
        assert ARMOR_CATEGORY_TO_DEFENSES["int_armour"] == frozenset({DefenseType.ENERGY_SHIELD})

        # Hybrid types
        str_dex_defenses = ARMOR_CATEGORY_TO_DEFENSES["str_dex_armour"]
        assert DefenseType.ARMOUR in str_dex_defenses
        assert DefenseType.EVASION in str_dex_defenses
        assert DefenseType.ENERGY_SHIELD not in str_dex_defenses

    def test_pob_to_db_category(self):
        """Test POB name to database category mapping."""
        assert POB_TO_DB_CATEGORY["One Handed Axe"] == "axe"
        assert POB_TO_DB_CATEGORY["Two Handed Sword"] == "sword"
        assert POB_TO_DB_CATEGORY["Bow"] == "bow"

    def test_category_to_trade_api(self):
        """Test category to trade API format mapping."""
        assert CATEGORY_TO_TRADE_API["sword"] == "weapon.sword"
        assert CATEGORY_TO_TRADE_API["body_armour"] == "armour.chest"
        assert CATEGORY_TO_TRADE_API["ring"] == "accessory.ring"

    def test_slot_to_categories(self):
        """Test slot to valid categories mapping."""
        body_cats = SLOT_TO_CATEGORIES[ItemSlot.BODY_ARMOUR.value]
        assert "str_armour" in body_cats
        assert "int_armour" in body_cats

        weapon_1h_cats = SLOT_TO_CATEGORIES[ItemSlot.WEAPONS_1H.value]
        assert "sword" in weapon_1h_cats
        assert "wand" in weapon_1h_cats


class TestItemClassification:
    """Test ItemClassification dataclass properties."""

    def test_is_weapon_sword(self):
        """Test sword is classified as weapon."""
        classification = classify_item("sword", "weapons - 1 hand")
        assert classification.is_weapon is True
        assert classification.is_armor is False
        assert classification.is_jewelry is False

    def test_is_weapon_bow(self):
        """Test bow is classified as weapon."""
        classification = classify_item("bow", "weapons - 2 hand")
        assert classification.is_weapon is True
        assert classification.is_ranged_weapon is True
        assert classification.is_melee_weapon is False

    def test_is_armor_str_armour(self):
        """Test str_armour is classified as armor."""
        classification = classify_item("str_armour", "body_armour")
        assert classification.is_armor is True
        assert classification.is_weapon is False
        assert classification.has_armour is True
        assert classification.has_evasion is False

    def test_is_armor_hybrid(self):
        """Test hybrid armor has multiple defense types."""
        classification = classify_item("str_dex_armour", "body_armour")
        assert classification.is_armor is True
        assert classification.has_armour is True
        assert classification.has_evasion is True
        assert classification.has_energy_shield is False

    def test_is_jewelry_ring(self):
        """Test ring is classified as jewelry."""
        classification = classify_item("ring", "ring")
        assert classification.is_jewelry is True
        assert classification.is_accessory is True  # alias
        assert classification.is_weapon is False

    def test_is_one_handed(self):
        """Test one-handed weapon detection."""
        classification = classify_item("sword", "weapons - 1 hand")
        assert classification.is_one_handed is True
        assert classification.is_two_handed is False

    def test_is_two_handed(self):
        """Test two-handed weapon detection."""
        classification = classify_item("bow", "weapons - 2 hand")
        assert classification.is_one_handed is False
        assert classification.is_two_handed is True

    def test_is_caster_weapon(self):
        """Test caster weapon detection."""
        staff = classify_item("staff", "weapons - 2 hand")
        assert staff.is_caster_weapon is True
        assert staff.is_attack_weapon is False

        wand = classify_item("wand", "weapons - 1 hand")
        assert wand.is_caster_weapon is True

        sword = classify_item("sword", "weapons - 1 hand")
        assert sword.is_caster_weapon is False
        assert sword.is_attack_weapon is True

    def test_weapon_class(self):
        """Test weapon class property."""
        staff = classify_item("staff", "weapons - 2 hand")
        assert staff.weapon_class == WeaponClass.CASTER

        bow = classify_item("bow", "weapons - 2 hand")
        assert bow.weapon_class == WeaponClass.RANGED

        sword = classify_item("sword", "weapons - 1 hand")
        assert sword.weapon_class == WeaponClass.MELEE

        ring = classify_item("ring", "ring")
        assert ring.weapon_class is None  # Not a weapon

    def test_is_offhand(self):
        """Test offhand detection."""
        shield = classify_item("shield", "shield")
        assert shield.is_offhand is True
        assert shield.is_shield is True

        quiver = classify_item("quiver", "quiver")
        assert quiver.is_offhand is True

    def test_defense_types(self):
        """Test defense types property."""
        str_armor = classify_item("str_armour", "body_armour")
        assert DefenseType.ARMOUR in str_armor.defense_types
        assert len(str_armor.defense_types) == 1

        hybrid = classify_item("str_int_armour", "body_armour")
        assert DefenseType.ARMOUR in hybrid.defense_types
        assert DefenseType.ENERGY_SHIELD in hybrid.defense_types
        assert len(hybrid.defense_types) == 2


class TestMatchesWeightKey:
    """Test ItemClassification.matches_weight_key method."""

    def test_direct_category_match(self):
        """Test direct category matching."""
        classification = classify_item("sword", "weapons - 1 hand")
        assert classification.matches_weight_key("sword") is True
        assert classification.matches_weight_key("axe") is False

    def test_direct_slot_match(self):
        """Test direct slot matching."""
        classification = classify_item("str_armour", "body_armour")
        assert classification.matches_weight_key("body_armour") is True

    def test_ranged_weight_key(self):
        """Test 'ranged' weight key matches bows and crossbows."""
        bow = classify_item("bow", "weapons - 2 hand")
        assert bow.matches_weight_key("ranged") is True

        sword = classify_item("sword", "weapons - 1 hand")
        assert sword.matches_weight_key("ranged") is False

    def test_one_hand_weapon_key(self):
        """Test 'one_hand_weapon' weight key."""
        sword = classify_item("sword", "weapons - 1 hand")
        assert sword.matches_weight_key("one_hand_weapon") is True

        # Caster weapons should not match
        wand = classify_item("wand", "weapons - 1 hand")
        assert wand.matches_weight_key("one_hand_weapon") is False

    def test_two_hand_weapon_key(self):
        """Test 'two_hand_weapon' weight key."""
        bow = classify_item("bow", "weapons - 2 hand")
        assert bow.matches_weight_key("two_hand_weapon") is True

        # Staff is caster, should not match
        staff = classify_item("staff", "weapons - 2 hand")
        assert staff.matches_weight_key("two_hand_weapon") is False

    def test_generic_weapon_key(self):
        """Test 'weapon' weight key excludes casters."""
        sword = classify_item("sword", "weapons - 1 hand")
        assert sword.matches_weight_key("weapon") is True

        wand = classify_item("wand", "weapons - 1 hand")
        assert wand.matches_weight_key("weapon") is False

    def test_armour_key(self):
        """Test 'armour' weight key."""
        classification = classify_item("str_armour", "body_armour")
        assert classification.matches_weight_key("armour") is True

    def test_jewellery_key(self):
        """Test 'jewellery' weight key."""
        ring = classify_item("ring", "ring")
        assert ring.matches_weight_key("jewellery") is True

        amulet = classify_item("amulet", "amulet")
        assert amulet.matches_weight_key("jewellery") is True

    def test_default_key(self):
        """Test 'default' weight key always matches."""
        sword = classify_item("sword", "weapons - 1 hand")
        assert sword.matches_weight_key("default") is True

        ring = classify_item("ring", "ring")
        assert ring.matches_weight_key("default") is True


class TestHelperFunctions:
    """Test helper functions."""

    def test_normalize_slot(self):
        """Test slot normalization."""
        assert normalize_slot("body") == "body_armour"
        assert normalize_slot("weapon - 1 hand") == "weapons - 1 hand"
        assert normalize_slot("body_armour") == "body_armour"  # Already normalized

    def test_normalize_category(self):
        """Test category normalization."""
        assert normalize_category("One Handed Axe") == "axe"
        assert normalize_category("Bow") == "bow"
        assert normalize_category("sword") == "sword"  # Already normalized

    def test_is_valid_weapon_category(self):
        """Test weapon category validation."""
        assert is_valid_weapon_category("sword") is True
        assert is_valid_weapon_category("bow") is True
        assert is_valid_weapon_category("ring") is False

    def test_is_valid_armor_category(self):
        """Test armor category validation."""
        assert is_valid_armor_category("str_armour") is True
        assert is_valid_armor_category("str_dex_armour") is True
        assert is_valid_armor_category("sword") is False

    def test_is_valid_jewelry_category(self):
        """Test jewelry category validation."""
        assert is_valid_jewelry_category("ring") is True
        assert is_valid_jewelry_category("amulet") is True
        assert is_valid_jewelry_category("sword") is False

    def test_get_categories_for_slot(self):
        """Test getting categories for a slot."""
        body_cats = get_categories_for_slot("body_armour")
        assert "str_armour" in body_cats
        assert "int_armour" in body_cats

    def test_is_defense_mod_applicable(self):
        """Test defense mod applicability."""
        # Str armour should only get Armour mods
        assert is_defense_mod_applicable("10% increased Armour", "str_armour") is True
        assert is_defense_mod_applicable("10% increased Evasion", "str_armour") is False

        # Hybrid armour should get both
        assert is_defense_mod_applicable("10% increased Armour and Evasion", "str_dex_armour") is True

        # Non-armor should pass all checks
        assert is_defense_mod_applicable("10% increased Evasion", "sword") is True


class TestClassifyItem:
    """Test classify_item factory function."""

    def test_classify_item_basic(self):
        """Test basic item classification."""
        classification = classify_item("sword", "weapons - 1 hand")
        assert isinstance(classification, ItemClassification)
        assert classification.category == "sword"
        assert classification.slot == "weapons - 1 hand"

    def test_classify_item_with_tags(self):
        """Test classification with tags."""
        classification = classify_item("sword", "weapons - 1 hand", tags=["onehand", "weapon"])
        assert "onehand" in classification.tags
        assert classification.is_one_handed is True
