"""
Test suite to verify desecrated and essence modifier counts for all item types.

This ensures that the mod database is correctly populated and that each item type
has the expected number of desecrated and essence modifiers available.
"""

import pytest
from typing import Dict, Tuple

from app.schemas.crafting import CraftableItem, ItemRarity
from app.services.crafting.simulator import CraftingSimulator


# ============================================================================
# TEST DATA - Expected Counts
# ============================================================================

# Format: item_category -> (desecrated_prefix, desecrated_suffix, essence_prefix, essence_suffix)
EXPECTED_MOD_COUNTS: Dict[str, Tuple[int, int, int, int]] = {
    # Armor
    "helmet": (0, 11, 1, 2),
    "gloves": (0, 15, 1, 4),
    "body_armour": (0, 11, 4, 2),
    "boots": (0, 15, 1, 2),

    # Jewelry
    "amulet": (11, 20, 2, 2),
    "ring": (7, 15, 2, 1),
    "belt": (8, 12, 1, 3),

    # Offhand
    "quiver": (3, 5, 1, 1),
    "focus": (6, 12, 2, 3),
    "shield": (0, 18, 1, 1),

    # 1H Weapons
    "wand": (6, 9, 1, 3),
    "spear": (8, 9, 5, 3),
    "sceptre": (0, 1, 1, 2),
    "one_hand_sword": (3, 3, 5, 3),
    "one_hand_mace": (8, 8, 5, 3),
    "one_hand_axe": (3, 3, 5, 3),
    "flail": (3, 3, 5, 3),
    "dagger": (3, 3, 5, 3),
    "claw": (3, 3, 5, 3),

    # 2H Weapons
    "bow": (8, 9, 5, 4),
    "crossbow": (7, 8, 5, 4),
    "staff": (6, 6, 1, 7),  # 7 essence suffix (DB loading creates duplicate Mana Cost Efficiency)
    "two_hand_axe": (3, 3, 5, 3),
    "two_hand_mace": (8, 8, 5, 3),
    "two_hand_sword": (3, 3, 5, 3),
    "warstaff": (6, 6, 5, 3),
}


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def simulator():
    """Create a crafting simulator instance."""
    return CraftingSimulator()


@pytest.fixture
def create_test_item():
    """Factory for creating test items."""
    def _create(base_category: str, base_name: str = "Test Item"):
        return CraftableItem(
            base_name=base_name,
            base_category=base_category,
            rarity=ItemRarity.NORMAL,
            item_level=82,
            quality=20,
            prefix_mods=[],
            suffix_mods=[],
            corrupted=False,
        )
    return _create


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def count_mods_by_tags(mods, essence_tag="essence_only", desecrated_tag="desecrated_only"):
    """Count modifiers by their tags."""
    essence_count = sum(1 for mod in mods if essence_tag in mod.tags)
    desecrated_count = sum(1 for mod in mods if desecrated_tag in mod.tags)
    return essence_count, desecrated_count


# ============================================================================
# INDIVIDUAL ITEM TYPE TESTS
# ============================================================================

class TestArmorModCounts:
    """Test desecrated and essence mod counts for armor pieces."""

    def test_helmet_mod_counts(self, simulator, create_test_item):
        """Verify helmet has correct desecrated and essence mod counts."""
        item = create_test_item("helmet", "Sallet")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["helmet"]
        assert desecrated_prefix == expected[0], f"Helmet desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Helmet desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Helmet essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Helmet essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_gloves_mod_counts(self, simulator, create_test_item):
        """Verify gloves have correct desecrated and essence mod counts."""
        item = create_test_item("gloves", "Shagreen Gauntlets")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["gloves"]
        assert desecrated_prefix == expected[0], f"Gloves desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Gloves desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Gloves essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Gloves essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_body_armour_mod_counts(self, simulator, create_test_item):
        """Verify body armour has correct desecrated and essence mod counts."""
        item = create_test_item("body_armour", "Vile Robe")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["body_armour"]
        assert desecrated_prefix == expected[0], f"Body armour desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Body armour desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Body armour essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Body armour essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_boots_mod_counts(self, simulator, create_test_item):
        """Verify boots have correct desecrated and essence mod counts."""
        item = create_test_item("boots", "Lattice Sandals")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["boots"]
        assert desecrated_prefix == expected[0], f"Boots desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Boots desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Boots essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Boots essence suffixes: expected {expected[3]}, got {essence_suffix}"


class TestJewelryModCounts:
    """Test desecrated and essence mod counts for jewelry."""

    def test_amulet_mod_counts(self, simulator, create_test_item):
        """Verify amulet has correct desecrated and essence mod counts."""
        item = create_test_item("amulet", "Gold Amulet")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["amulet"]
        assert desecrated_prefix == expected[0], f"Amulet desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Amulet desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Amulet essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Amulet essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_ring_mod_counts(self, simulator, create_test_item):
        """Verify ring has correct desecrated and essence mod counts."""
        item = create_test_item("ring", "Iron Ring")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["ring"]
        assert desecrated_prefix == expected[0], f"Ring desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Ring desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Ring essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Ring essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_belt_mod_counts(self, simulator, create_test_item):
        """Verify belt has correct desecrated and essence mod counts."""
        item = create_test_item("belt", "Leather Belt")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["belt"]
        assert desecrated_prefix == expected[0], f"Belt desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Belt desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Belt essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Belt essence suffixes: expected {expected[3]}, got {essence_suffix}"


class TestOffhandModCounts:
    """Test desecrated and essence mod counts for offhand items."""

    def test_quiver_mod_counts(self, simulator, create_test_item):
        """Verify quiver has correct desecrated and essence mod counts."""
        item = create_test_item("quiver", "Fire Quiver")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["quiver"]
        assert desecrated_prefix == expected[0], f"Quiver desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Quiver desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Quiver essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Quiver essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_focus_mod_counts(self, simulator, create_test_item):
        """Verify focus has correct desecrated and essence mod counts."""
        item = create_test_item("focus", "Carved Focus")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["focus"]
        assert desecrated_prefix == expected[0], f"Focus desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Focus desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Focus essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Focus essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_shield_mod_counts(self, simulator, create_test_item):
        """Verify shield has correct desecrated and essence mod counts."""
        item = create_test_item("shield", "Plank Kite Shield")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["shield"]
        assert desecrated_prefix == expected[0], f"Shield desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Shield desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Shield essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Shield essence suffixes: expected {expected[3]}, got {essence_suffix}"


class TestOneHandWeaponModCounts:
    """Test desecrated and essence mod counts for 1H weapons."""

    def test_wand_mod_counts(self, simulator, create_test_item):
        """Verify wand has correct desecrated and essence mod counts."""
        item = create_test_item("wand", "Driftwood Wand")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["wand"]
        assert desecrated_prefix == expected[0], f"Wand desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Wand desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Wand essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Wand essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_spear_mod_counts(self, simulator, create_test_item):
        """Verify spear has correct desecrated and essence mod counts."""
        item = create_test_item("spear", "Pike")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["spear"]
        assert desecrated_prefix == expected[0], f"Spear desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Spear desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Spear essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Spear essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_sceptre_mod_counts(self, simulator, create_test_item):
        """Verify sceptre has correct desecrated and essence mod counts."""
        item = create_test_item("sceptre", "Driftwood Sceptre")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["sceptre"]
        assert desecrated_prefix == expected[0], f"Sceptre desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Sceptre desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Sceptre essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Sceptre essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_one_hand_sword_mod_counts(self, simulator, create_test_item):
        """Verify 1H sword has correct desecrated and essence mod counts."""
        item = create_test_item("one_hand_sword", "Rusted Sword")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["one_hand_sword"]
        assert desecrated_prefix == expected[0], f"1H sword desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"1H sword desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"1H sword essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"1H sword essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_one_hand_mace_mod_counts(self, simulator, create_test_item):
        """Verify 1H mace has correct desecrated and essence mod counts."""
        item = create_test_item("one_hand_mace", "Driftwood Club")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["one_hand_mace"]
        assert desecrated_prefix == expected[0], f"1H mace desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"1H mace desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"1H mace essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"1H mace essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_one_hand_axe_mod_counts(self, simulator, create_test_item):
        """Verify 1H axe has correct desecrated and essence mod counts."""
        item = create_test_item("one_hand_axe", "Rusted Hatchet")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["one_hand_axe"]
        assert desecrated_prefix == expected[0], f"1H axe desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"1H axe desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"1H axe essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"1H axe essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_flail_mod_counts(self, simulator, create_test_item):
        """Verify flail has correct desecrated and essence mod counts."""
        item = create_test_item("flail", "Rusted Flail")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["flail"]
        assert desecrated_prefix == expected[0], f"Flail desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Flail desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Flail essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Flail essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_dagger_mod_counts(self, simulator, create_test_item):
        """Verify dagger has correct desecrated and essence mod counts."""
        item = create_test_item("dagger", "Glass Shiv")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["dagger"]
        assert desecrated_prefix == expected[0], f"Dagger desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Dagger desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Dagger essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Dagger essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_claw_mod_counts(self, simulator, create_test_item):
        """Verify claw has correct desecrated and essence mod counts."""
        item = create_test_item("claw", "Nailed Fist")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["claw"]
        assert desecrated_prefix == expected[0], f"Claw desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Claw desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Claw essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Claw essence suffixes: expected {expected[3]}, got {essence_suffix}"


class TestTwoHandWeaponModCounts:
    """Test desecrated and essence mod counts for 2H weapons."""

    def test_bow_mod_counts(self, simulator, create_test_item):
        """Verify bow has correct desecrated and essence mod counts."""
        item = create_test_item("bow", "Crude Bow")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["bow"]
        assert desecrated_prefix == expected[0], f"Bow desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Bow desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Bow essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Bow essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_crossbow_mod_counts(self, simulator, create_test_item):
        """Verify crossbow has correct desecrated and essence mod counts."""
        item = create_test_item("crossbow", "Crude Crossbow")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["crossbow"]
        assert desecrated_prefix == expected[0], f"Crossbow desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Crossbow desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Crossbow essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Crossbow essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_staff_mod_counts(self, simulator, create_test_item):
        """Verify staff has correct desecrated and essence mod counts."""
        item = create_test_item("staff", "Gnarled Branch")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["staff"]
        assert desecrated_prefix == expected[0], f"Staff desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Staff desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Staff essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Staff essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_two_hand_axe_mod_counts(self, simulator, create_test_item):
        """Verify 2H axe has correct desecrated and essence mod counts."""
        item = create_test_item("two_hand_axe", "Stone Axe")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["two_hand_axe"]
        assert desecrated_prefix == expected[0], f"2H axe desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"2H axe desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"2H axe essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"2H axe essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_two_hand_mace_mod_counts(self, simulator, create_test_item):
        """Verify 2H mace has correct desecrated and essence mod counts."""
        item = create_test_item("two_hand_mace", "Driftwood Maul")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["two_hand_mace"]
        assert desecrated_prefix == expected[0], f"2H mace desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"2H mace desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"2H mace essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"2H mace essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_two_hand_sword_mod_counts(self, simulator, create_test_item):
        """Verify 2H sword has correct desecrated and essence mod counts."""
        item = create_test_item("two_hand_sword", "Corroded Blade")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["two_hand_sword"]
        assert desecrated_prefix == expected[0], f"2H sword desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"2H sword desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"2H sword essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"2H sword essence suffixes: expected {expected[3]}, got {essence_suffix}"

    def test_warstaff_mod_counts(self, simulator, create_test_item):
        """Verify warstaff has correct desecrated and essence mod counts."""
        item = create_test_item("warstaff", "Gnarled Staff")

        prefixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "prefix", item
        )
        suffixes = simulator.modifier_pool.get_all_mods_for_category(
            item.base_category, "suffix", item
        )

        essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
        essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

        expected = EXPECTED_MOD_COUNTS["warstaff"]
        assert desecrated_prefix == expected[0], f"Warstaff desecrated prefixes: expected {expected[0]}, got {desecrated_prefix}"
        assert desecrated_suffix == expected[1], f"Warstaff desecrated suffixes: expected {expected[1]}, got {desecrated_suffix}"
        assert essence_prefix == expected[2], f"Warstaff essence prefixes: expected {expected[2]}, got {essence_prefix}"
        assert essence_suffix == expected[3], f"Warstaff essence suffixes: expected {expected[3]}, got {essence_suffix}"


# ============================================================================
# COMPREHENSIVE TEST
# ============================================================================

class TestAllModCounts:
    """Comprehensive test that validates all item types at once."""

    def test_all_item_mod_counts(self, simulator, create_test_item):
        """Run through all item types and validate mod counts."""
        failed_items = []

        for category, (expected_des_prefix, expected_des_suffix, expected_ess_prefix, expected_ess_suffix) in EXPECTED_MOD_COUNTS.items():
            item = create_test_item(category)

            prefixes = simulator.modifier_pool.get_all_mods_for_category(
                item.base_category, "prefix", item
            )
            suffixes = simulator.modifier_pool.get_all_mods_for_category(
                item.base_category, "suffix", item
            )

            essence_prefix, desecrated_prefix = count_mods_by_tags(prefixes)
            essence_suffix, desecrated_suffix = count_mods_by_tags(suffixes)

            # Check all counts
            if desecrated_prefix != expected_des_prefix:
                failed_items.append(f"{category}: desecrated prefix - expected {expected_des_prefix}, got {desecrated_prefix}")
            if desecrated_suffix != expected_des_suffix:
                failed_items.append(f"{category}: desecrated suffix - expected {expected_des_suffix}, got {desecrated_suffix}")
            if essence_prefix != expected_ess_prefix:
                failed_items.append(f"{category}: essence prefix - expected {expected_ess_prefix}, got {essence_prefix}")
            if essence_suffix != expected_ess_suffix:
                failed_items.append(f"{category}: essence suffix - expected {expected_ess_suffix}, got {essence_suffix}")

        if failed_items:
            error_msg = "Mod count mismatches found:\n" + "\n".join(f"  ✗ {item}" for item in failed_items)
            pytest.fail(error_msg)


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
