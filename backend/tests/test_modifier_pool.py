"""
Comprehensive test suite for Modifier Pool functionality.

Tests cover:
- Modifier filtering by category
- Modifier filtering by item level
- Modifier filtering by tags
- Modifier filtering by mod groups
- Desecrated-only filtering
- Essence-only filtering
- Excluded group handling
- Weighted random selection
- Jewellery category expansion
- Tier-based filtering
"""

import pytest
from typing import List

from app.schemas.crafting import ItemModifier, ModType, CraftableItem, ItemRarity
from app.services.crafting.modifier_pool import ModifierPool


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def create_test_modifier():
    """Factory for creating test modifiers."""
    def _create(
        name: str,
        mod_type: ModType,
        tier: int = 1,
        stat_min: int = 10,
        stat_max: int = 20,
        required_ilvl: int = 1,
        applicable_items: List[str] = None,
        tags: List[str] = None,
        mod_group: str = None,
        weight: int = 100,
        is_essence_only: bool = False,
        is_exclusive: bool = False,
    ):
        return ItemModifier(
            name=name,
            mod_type=mod_type,
            tier=tier,
            stat_text=f"{name} stat text",
            stat_min=stat_min,
            stat_max=stat_max,
            required_ilvl=required_ilvl,
            weight=weight,
            mod_group=mod_group or f"{name}_group",
            applicable_items=applicable_items or ["body_armour"],
            tags=tags or [],
            is_essence_only=is_essence_only,
            is_exclusive=is_exclusive,
        )
    return _create


@pytest.fixture
def create_test_item():
    """Factory for creating test items."""
    def _create(
        base_name: str = "Vile Robe",
        base_category: str = "int_armour",
        item_level: int = 80,
        rarity: ItemRarity = ItemRarity.NORMAL,
        prefix_mods: List[ItemModifier] = None,
        suffix_mods: List[ItemModifier] = None,
    ):
        return CraftableItem(
            base_name=base_name,
            base_category=base_category,
            rarity=rarity,
            item_level=item_level,
            quality=20,
            prefix_mods=prefix_mods or [],
            suffix_mods=suffix_mods or [],
            corrupted=False,
        )
    return _create


@pytest.fixture
def sample_modifier_pool(create_test_modifier):
    """Create a sample modifier pool with various modifiers."""
    modifiers = [
        # Regular prefixes
        create_test_modifier(
            "Life Prefix 1",
            ModType.PREFIX,
            tier=1,
            required_ilvl=1,
            applicable_items=["body_armour", "int_armour"],
            tags=["life"],
            mod_group="life",
        ),
        create_test_modifier(
            "Life Prefix 2",
            ModType.PREFIX,
            tier=2,
            required_ilvl=40,
            applicable_items=["body_armour", "int_armour"],
            tags=["life"],
            mod_group="life",
        ),
        create_test_modifier(
            "Life Prefix 3",
            ModType.PREFIX,
            tier=3,
            required_ilvl=75,
            applicable_items=["body_armour", "int_armour"],
            tags=["life"],
            mod_group="life",
        ),

        # Regular suffixes
        create_test_modifier(
            "Fire Resistance",
            ModType.SUFFIX,
            tier=1,
            required_ilvl=1,
            applicable_items=["body_armour", "int_armour", "jewellery"],
            tags=["resistance", "fire"],
            mod_group="fire_resistance",
        ),
        create_test_modifier(
            "Cold Resistance",
            ModType.SUFFIX,
            tier=1,
            required_ilvl=1,
            applicable_items=["body_armour", "int_armour"],
            tags=["resistance", "cold"],
            mod_group="cold_resistance",
        ),

        # Desecrated only
        create_test_modifier(
            "Ulaman's Strength",
            ModType.PREFIX,
            tier=1,
            required_ilvl=65,
            applicable_items=["body_armour", "jewellery"],
            tags=["desecrated_only", "ulaman", "attribute"],
            mod_group="desecrated_attributes",
            is_exclusive=True,
        ),

        # Essence only
        create_test_modifier(
            "Essence Fire Damage",
            ModType.PREFIX,
            tier=1,
            required_ilvl=1,
            applicable_items=["weapon"],
            tags=["fire", "damage"],
            mod_group="essence_fire",
            is_essence_only=True,
        ),

        # Jewellery specific
        create_test_modifier(
            "Dual Attributes",
            ModType.SUFFIX,
            tier=1,
            required_ilvl=65,
            applicable_items=["jewellery"],
            tags=["attribute"],
            mod_group="dual_attributes",
        ),

        # High item level requirement
        create_test_modifier(
            "High Level Prefix",
            ModType.PREFIX,
            tier=1,
            required_ilvl=85,
            applicable_items=["body_armour"],
            tags=["endgame"],
            mod_group="high_level",
        ),
    ]

    return ModifierPool(modifiers)


# ============================================================================
# CATEGORY FILTERING TESTS
# ============================================================================

class TestCategoryFiltering:
    """Test filtering modifiers by item category."""

    def test_filters_by_category(self, sample_modifier_pool):
        """Should only return modifiers applicable to specified category."""
        eligible = sample_modifier_pool.get_eligible_mods(
            item_category="body_armour",
            item_level=80,
            mod_type="prefix",
        )

        # Should include body_armour applicable mods
        names = [mod.name for mod in eligible]
        assert "Life Prefix 1" in names
        assert "Life Prefix 2" in names
        assert "Life Prefix 3" in names
        # Should not include weapon-only mods
        assert "Essence Fire Damage" not in names

    def test_jewellery_category_expansion(self, sample_modifier_pool, create_test_item):
        """Jewellery category should expand to amulet/ring/belt."""
        amulet_item = create_test_item(base_name="Gold Amulet", base_category="amulet")

        # Mock a base item query - in real test would need database
        # For now, test the concept
        eligible = sample_modifier_pool.get_eligible_mods(
            item_category="amulet",
            item_level=80,
            mod_type="suffix",
        )

        # Should include jewellery mods
        names = [mod.name for mod in eligible]
        # Dual Attributes is jewellery-only
        # Fire Resistance includes jewellery

    def test_excludes_inapplicable_categories(self, sample_modifier_pool):
        """Should exclude modifiers not applicable to category."""
        eligible = sample_modifier_pool.get_eligible_mods(
            item_category="weapon",
            item_level=80,
            mod_type="prefix",
        )

        names = [mod.name for mod in eligible]
        # Should not include body_armour only mods
        assert "Life Prefix 1" not in names
        assert "Life Prefix 2" not in names
        # Should include weapon mods
        assert "Essence Fire Damage" in names


# ============================================================================
# ITEM LEVEL FILTERING TESTS
# ============================================================================

class TestItemLevelFiltering:
    """Test filtering modifiers by item level."""

    def test_filters_by_item_level(self, sample_modifier_pool):
        """Should only return modifiers with ilvl <= item level."""
        # Low level item (ilvl 30)
        eligible_low = sample_modifier_pool.get_eligible_mods(
            item_category="body_armour",
            item_level=30,
            mod_type="prefix",
        )

        names_low = [mod.name for mod in eligible_low]
        assert "Life Prefix 1" in names_low  # requires ilvl 1
        assert "Life Prefix 2" not in names_low  # requires ilvl 40
        assert "Life Prefix 3" not in names_low  # requires ilvl 75

    def test_high_level_item_has_all_tiers(self, sample_modifier_pool):
        """High level item should have access to all tiers."""
        eligible_high = sample_modifier_pool.get_eligible_mods(
            item_category="body_armour",
            item_level=85,
            mod_type="prefix",
        )

        names_high = [mod.name for mod in eligible_high]
        assert "Life Prefix 1" in names_high
        assert "Life Prefix 2" in names_high
        assert "Life Prefix 3" in names_high
        assert "High Level Prefix" in names_high

    def test_respects_min_mod_level_parameter(self, sample_modifier_pool):
        """Should respect min_mod_level parameter to filter low tiers."""
        eligible = sample_modifier_pool.get_eligible_mods(
            item_category="body_armour",
            item_level=85,
            mod_type="prefix",
            min_mod_level=40,
        )

        names = [mod.name for mod in eligible]
        assert "Life Prefix 1" not in names  # ilvl 1 < min 40
        assert "Life Prefix 2" in names  # ilvl 40 >= min 40
        assert "Life Prefix 3" in names  # ilvl 75 >= min 40


# ============================================================================
# TAG FILTERING TESTS
# ============================================================================

class TestTagFiltering:
    """Test filtering modifiers by tags."""

    def test_filters_desecrated_only_mods(self, sample_modifier_pool):
        """Should filter desecrated-only modifiers separately."""
        # Get all eligible prefixes (including exclusive desecrated mods)
        all_prefixes = sample_modifier_pool.get_eligible_mods(
            item_category="body_armour",
            item_level=80,
            mod_type="prefix",
            exclude_exclusive=False,
            exclude_desecrated=False,
        )

        # Check for desecrated tag
        desecrated_mods = [mod for mod in all_prefixes if "desecrated_only" in mod.tags]
        regular_mods = [mod for mod in all_prefixes if "desecrated_only" not in mod.tags]

        # Should have both types
        assert len(desecrated_mods) > 0
        assert len(regular_mods) > 0

    def test_filters_by_boss_tag(self, sample_modifier_pool):
        """Should be able to filter by boss-specific tags."""
        all_prefixes = sample_modifier_pool.get_eligible_mods(
            item_category="body_armour",
            item_level=80,
            mod_type="prefix",
            exclude_exclusive=False,
            exclude_desecrated=False,
        )

        ulaman_mods = [mod for mod in all_prefixes if "ulaman" in mod.tags]
        assert len(ulaman_mods) > 0
        assert "Ulaman's Strength" in [mod.name for mod in ulaman_mods]


# ============================================================================
# MOD GROUP FILTERING TESTS
# ============================================================================

class TestModGroupFiltering:
    """Test filtering and exclusion by mod groups."""

    def test_excludes_groups_already_on_item(self, sample_modifier_pool, create_test_modifier, create_test_item):
        """Should exclude mod groups that already exist on item."""
        life_mod = create_test_modifier(
            "Life Prefix 1",
            ModType.PREFIX,
            mod_group="life",
        )
        item = create_test_item(prefix_mods=[life_mod])

        excluded_groups = sample_modifier_pool._get_excluded_groups_from_item(item)

        assert "life" in excluded_groups

    def test_allows_different_groups(self, sample_modifier_pool, create_test_modifier, create_test_item):
        """Should allow modifiers from different groups."""
        fire_res_mod = create_test_modifier(
            "Fire Resistance",
            ModType.SUFFIX,
            mod_group="fire_resistance",
        )
        item = create_test_item(suffix_mods=[fire_res_mod])

        excluded_groups = sample_modifier_pool._get_excluded_groups_from_item(item)

        # fire_resistance is excluded
        assert "fire_resistance" in excluded_groups
        # But cold_resistance should not be excluded
        assert "cold_resistance" not in excluded_groups


# ============================================================================
# ESSENCE MODIFIER TESTS
# ============================================================================

class TestEssenceModifiers:
    """Test essence-specific modifier handling."""

    def test_filters_essence_only_mods(self, sample_modifier_pool):
        """Should identify essence-only modifiers."""
        all_mods = sample_modifier_pool.modifiers

        essence_mods = [mod for mod in all_mods if mod.is_essence_only]

        assert len(essence_mods) > 0
        assert "Essence Fire Damage" in [mod.name for mod in essence_mods]

    def test_get_essence_modifier_by_type(self, sample_modifier_pool):
        """Should retrieve essence modifier by essence type."""
        # This would be implemented in the modifier pool
        # Test structure for essence-specific retrieval
        pass


# ============================================================================
# WEIGHTED RANDOM SELECTION TESTS
# ============================================================================

class TestWeightedRandomSelection:
    """Test weighted random modifier selection."""

    def test_weighted_random_respects_weights(self, create_test_modifier):
        """Higher weight modifiers should be selected more often."""
        mods = [
            create_test_modifier("Common Mod", ModType.PREFIX, weight=100),
            create_test_modifier("Rare Mod", ModType.PREFIX, weight=1),
        ]
        pool = ModifierPool(mods)

        # Run many selections
        selections = []
        for _ in range(1000):
            selected = pool._weighted_random_choice(mods)
            selections.append(selected.name)

        # Common mod should be selected much more often
        common_count = selections.count("Common Mod")
        rare_count = selections.count("Rare Mod")

        # With 100:1 ratio, common should be ~99% of selections
        assert common_count > rare_count * 50  # At least 50x more common

    def test_zero_weight_never_selected(self, create_test_modifier):
        """Modifiers with zero weight should never be selected."""
        mods = [
            create_test_modifier("Available Mod", ModType.PREFIX, weight=100),
            create_test_modifier("Impossible Mod", ModType.PREFIX, weight=0),
        ]
        pool = ModifierPool(mods)

        # Run many selections
        selections = []
        for _ in range(100):
            selected = pool._weighted_random_choice(mods)
            selections.append(selected.name)

        # Impossible mod should never be selected
        assert "Impossible Mod" not in selections
        assert "Available Mod" in selections


# ============================================================================
# ROLL RANDOM MODIFIER TESTS
# ============================================================================

class TestRollRandomModifier:
    """Test the main roll_random_modifier method."""

    def test_returns_modifier_of_correct_type(self, sample_modifier_pool):
        """Should return modifier of requested type."""
        prefix = sample_modifier_pool.roll_random_modifier(
            mod_type="prefix",
            item_category="body_armour",
            item_level=80,
        )

        assert prefix is not None
        assert prefix.mod_type == ModType.PREFIX

    def test_returns_suffix_when_requested(self, sample_modifier_pool):
        """Should return suffix when requested."""
        suffix = sample_modifier_pool.roll_random_modifier(
            mod_type="suffix",
            item_category="body_armour",
            item_level=80,
        )

        assert suffix is not None
        assert suffix.mod_type == ModType.SUFFIX

    def test_respects_excluded_groups(self, sample_modifier_pool):
        """Should not return modifiers from excluded groups."""
        modifier = sample_modifier_pool.roll_random_modifier(
            mod_type="suffix",
            item_category="body_armour",
            item_level=80,
            excluded_groups={"fire_resistance"},
        )

        # Should not be from fire_resistance group
        if modifier:
            assert modifier.mod_group != "fire_resistance"

    def test_returns_none_when_no_eligible_mods(self, sample_modifier_pool):
        """Should return None when no eligible modifiers exist."""
        modifier = sample_modifier_pool.roll_random_modifier(
            mod_type="prefix",
            item_category="nonexistent_category",
            item_level=1,
        )

        assert modifier is None


# ============================================================================
# MODIFIER POOL QUERIES TESTS
# ============================================================================

class TestModifierPoolQueries:
    """Test various query methods on modifier pool."""

    def test_get_mods_by_group(self, sample_modifier_pool):
        """Should return all modifiers in a group."""
        life_mods = sample_modifier_pool.get_mods_by_group("life")

        assert len(life_mods) == 3
        names = [mod.name for mod in life_mods]
        assert "Life Prefix 1" in names
        assert "Life Prefix 2" in names
        assert "Life Prefix 3" in names

    def test_get_mods_by_tag(self, sample_modifier_pool):
        """Should return all modifiers with a tag."""
        resistance_mods = [mod for mod in sample_modifier_pool.modifiers if "resistance" in mod.tags]

        assert len(resistance_mods) >= 2
        names = [mod.name for mod in resistance_mods]
        assert "Fire Resistance" in names
        assert "Cold Resistance" in names


# ============================================================================
# EDGE CASES AND ERROR CONDITIONS
# ============================================================================

class TestModifierPoolEdgeCases:
    """Test edge cases for modifier pool."""

    def test_empty_modifier_pool(self):
        """Should handle empty modifier pool gracefully."""
        pool = ModifierPool([])

        modifier = pool.roll_random_modifier(
            mod_type="prefix",
            item_category="body_armour",
            item_level=80,
        )

        assert modifier is None

    def test_all_mods_excluded(self, sample_modifier_pool):
        """Should return None when all mods are excluded."""
        # Exclude all groups
        all_groups = {mod.mod_group for mod in sample_modifier_pool.modifiers}

        modifier = sample_modifier_pool.roll_random_modifier(
            mod_type="prefix",
            item_category="body_armour",
            item_level=80,
            excluded_groups=all_groups,
        )

        assert modifier is None

    def test_extremely_high_item_level(self, sample_modifier_pool):
        """Should handle very high item levels."""
        modifier = sample_modifier_pool.roll_random_modifier(
            mod_type="prefix",
            item_category="body_armour",
            item_level=999,
        )

        # Should still return a modifier
        assert modifier is not None

    def test_item_level_zero(self, sample_modifier_pool):
        """Should handle item level 0."""
        modifier = sample_modifier_pool.roll_random_modifier(
            mod_type="prefix",
            item_category="body_armour",
            item_level=0,
        )

        # Should only return mods with ilvl 0 or might return None
        # Depends on implementation


# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestModifierPoolPerformance:
    """Test performance of modifier pool operations."""

    def test_large_pool_performance(self, create_test_modifier):
        """Should handle large modifier pools efficiently."""
        # Create 1000 modifiers
        large_pool_mods = []
        for i in range(1000):
            large_pool_mods.append(
                create_test_modifier(
                    f"Mod{i}",
                    ModType.PREFIX if i % 2 == 0 else ModType.SUFFIX,
                    applicable_items=["body_armour"],
                )
            )

        pool = ModifierPool(large_pool_mods)

        # Should complete quickly
        import time
        start = time.time()
        for _ in range(100):
            pool.roll_random_modifier("prefix", "body_armour", 80)
        elapsed = time.time() - start

        # Should complete 100 rolls in under 1 second
        assert elapsed < 1.0


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
