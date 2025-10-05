"""
Comprehensive test suite for Exclusion Group functionality.

Tests cover:
- Exclusion group assignment from configuration
- Group 1: Dexterity attribute mods
- Group 2: Intelligence attribute mods and Dex+Int hybrid
- Group 3: All skill level modifiers (Spell/Projectile/Melee/Minion)
- Group 4: Strength attribute mods and Str hybrid mods
- Exclusion group filtering in modifier pool
- Exclusion group filtering in available mods
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
    """Factory for creating test modifiers with exclusion groups."""
    def _create(
        name: str,
        mod_type: ModType,
        stat_text: str,
        exclusion_group: int = None,
        tier: int = 1,
        stat_min: int = 10,
        stat_max: int = 20,
        required_ilvl: int = 1,
        applicable_items: List[str] = None,
        tags: List[str] = None,
        mod_group: str = None,
        weight: int = 100,
    ):
        return ItemModifier(
            name=name,
            mod_type=mod_type,
            tier=tier,
            stat_text=stat_text,
            stat_min=stat_min,
            stat_max=stat_max,
            required_ilvl=required_ilvl,
            weight=weight,
            mod_group=mod_group or f"{name}_group",
            applicable_items=applicable_items or ["amulet"],
            tags=tags or [],
            exclusion_group=exclusion_group,
        )
    return _create


@pytest.fixture
def create_test_item():
    """Factory for creating test items."""
    def _create(
        base_name: str = "Turquoise Amulet",
        base_category: str = "amulet",
        item_level: int = 82,
        rarity: ItemRarity = ItemRarity.MAGIC,
        prefix_mods: List[ItemModifier] = None,
        suffix_mods: List[ItemModifier] = None,
    ):
        return CraftableItem(
            base_name=base_name,
            base_category=base_category,
            rarity=rarity,
            item_level=item_level,
            quality=0,
            prefix_mods=prefix_mods or [],
            suffix_mods=suffix_mods or [],
            corrupted=False,
        )
    return _create


@pytest.fixture
def exclusion_group_modifiers(create_test_modifier):
    """Create a sample set of modifiers with exclusion groups matching screenshots."""
    return [
        # Group 1: Dexterity
        create_test_modifier(
            "Dexterity T1",
            ModType.SUFFIX,
            "+20 to Dexterity",
            exclusion_group=1,
            mod_group="dexterity",
        ),
        create_test_modifier(
            "Dexterity T2",
            ModType.SUFFIX,
            "+15 to Dexterity",
            exclusion_group=1,
            mod_group="dexterity",
        ),

        # Group 2: Intelligence and Dex+Int hybrid
        create_test_modifier(
            "Intelligence T1",
            ModType.SUFFIX,
            "+20 to Intelligence",
            exclusion_group=2,
            mod_group="intelligence",
        ),
        create_test_modifier(
            "Dex+Int Hybrid",
            ModType.SUFFIX,
            "+(9-15) to Dexterity and Intelligence",
            exclusion_group=2,
        ),

        # Group 3: Skill level mods
        create_test_modifier(
            "Spell Skills T1",
            ModType.SUFFIX,
            "+1 to Level of all Spell Skills",
            exclusion_group=3,
        ),
        create_test_modifier(
            "Projectile Skills T1",
            ModType.SUFFIX,
            "+1 to Level of all Projectile Skills",
            exclusion_group=3,
        ),
        create_test_modifier(
            "Melee Skills T1",
            ModType.SUFFIX,
            "+1 to Level of all Melee Skills",
            exclusion_group=3,
        ),
        create_test_modifier(
            "Minion Skills T1",
            ModType.SUFFIX,
            "+1 to Level of all Minion Skills",
            exclusion_group=3,
        ),
        create_test_modifier(
            "All Skills (Ulaman)",
            ModType.SUFFIX,
            "+1 to Level of all Skills",
            exclusion_group=3,
            tags=["ulaman"],
        ),

        # Group 4: Strength and Str hybrid mods
        create_test_modifier(
            "Strength T1",
            ModType.SUFFIX,
            "+20 to Strength",
            exclusion_group=4,
            mod_group="strength",
        ),
        create_test_modifier(
            "Str+Dex Hybrid",
            ModType.SUFFIX,
            "+(9-15) to Strength and Dexterity",
            exclusion_group=4,
        ),
        create_test_modifier(
            "Str+Int Hybrid",
            ModType.SUFFIX,
            "+(9-15) to Strength and Intelligence",
            exclusion_group=4,
        ),

        # Unrelated mod without exclusion group
        create_test_modifier(
            "Life Mod",
            ModType.PREFIX,
            "+50 to maximum Life",
            exclusion_group=None,
        ),
    ]


@pytest.fixture
def modifier_pool_with_exclusions(exclusion_group_modifiers):
    """Create a modifier pool with exclusion group modifiers."""
    return ModifierPool(exclusion_group_modifiers)


# ============================================================================
# TESTS: Exclusion Group Assignment
# ============================================================================

@pytest.mark.unit
class TestExclusionGroupAssignment:
    """Test that exclusion groups are correctly assigned to modifiers."""

    def test_dexterity_mods_have_group_1(self, exclusion_group_modifiers):
        """Test that Dexterity mods are assigned to group 1."""
        dex_mods = [m for m in exclusion_group_modifiers if "Dexterity" in m.stat_text and "Intelligence" not in m.stat_text and "Strength" not in m.stat_text]

        assert len(dex_mods) > 0, "No Dexterity mods found"
        for mod in dex_mods:
            assert mod.exclusion_group == 1, f"{mod.name} should have exclusion_group=1"

    def test_intelligence_mods_have_group_2(self, exclusion_group_modifiers):
        """Test that Intelligence mods (including Dex+Int hybrid) are assigned to group 2."""
        # Only pure Intelligence and Dex+Int hybrid (NOT Str+Int hybrid which is in Group 4)
        int_mods = [m for m in exclusion_group_modifiers if "Intelligence" in m.stat_text and "Strength" not in m.stat_text]

        assert len(int_mods) > 0, "No Intelligence mods found"
        for mod in int_mods:
            assert mod.exclusion_group == 2, f"{mod.name} should have exclusion_group=2"

    def test_skill_level_mods_have_group_3(self, exclusion_group_modifiers):
        """Test that all skill level mods are assigned to group 3."""
        skill_mods = [m for m in exclusion_group_modifiers if "to Level of all" in m.stat_text]

        assert len(skill_mods) > 0, "No skill level mods found"
        for mod in skill_mods:
            assert mod.exclusion_group == 3, f"{mod.name} should have exclusion_group=3"

    def test_strength_mods_have_group_4(self, exclusion_group_modifiers):
        """Test that Strength mods (including hybrids) are assigned to group 4."""
        str_mods = [m for m in exclusion_group_modifiers if "Strength" in m.stat_text]

        assert len(str_mods) > 0, "No Strength mods found"
        for mod in str_mods:
            assert mod.exclusion_group == 4, f"{mod.name} should have exclusion_group=4"

    def test_unrelated_mod_has_no_exclusion_group(self, exclusion_group_modifiers):
        """Test that mods without exclusion requirements have no group."""
        life_mod = next(m for m in exclusion_group_modifiers if "Life" in m.stat_text)

        assert life_mod.exclusion_group is None, "Life mod should not have exclusion_group"


# ============================================================================
# TESTS: Group 1 - Dexterity
# ============================================================================

@pytest.mark.unit
class TestGroup1DexterityExclusion:
    """Test Group 1: Dexterity attribute mods cannot coexist."""

    def test_dexterity_blocks_other_dexterity(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that having one Dexterity mod blocks other Dexterity mods."""
        # Create item with Dexterity T1
        dex_mod = create_test_modifier(
            "Dexterity T1",
            ModType.SUFFIX,
            "+20 to Dexterity",
            exclusion_group=1,
        )
        item = create_test_item(suffix_mods=[dex_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check no Dexterity mods are available
        dex_mods = [m for m in available if "Dexterity" in m.stat_text and "Intelligence" not in m.stat_text and "Strength" not in m.stat_text]
        assert len(dex_mods) == 0, f"Found {len(dex_mods)} Dexterity mods, expected 0"


# ============================================================================
# TESTS: Group 2 - Intelligence and Dex+Int
# ============================================================================

@pytest.mark.unit
class TestGroup2IntelligenceExclusion:
    """Test Group 2: Intelligence and Dex+Int hybrid mods cannot coexist."""

    def test_intelligence_blocks_dex_int_hybrid(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that Intelligence mod blocks Dex+Int hybrid."""
        # Create item with Intelligence
        int_mod = create_test_modifier(
            "Intelligence T1",
            ModType.SUFFIX,
            "+20 to Intelligence",
            exclusion_group=2,
        )
        item = create_test_item(suffix_mods=[int_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check no Group 2 Intelligence mods are available (excluding Str+Int which is Group 4)
        int_mods = [m for m in available if "Intelligence" in m.stat_text and "Strength" not in m.stat_text]
        assert len(int_mods) == 0, f"Found {len(int_mods)} Intelligence mods, expected 0"

    def test_dex_int_hybrid_blocks_pure_intelligence(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that Dex+Int hybrid blocks pure Intelligence."""
        # Create item with Dex+Int hybrid
        hybrid_mod = create_test_modifier(
            "Dex+Int Hybrid",
            ModType.SUFFIX,
            "+(9-15) to Dexterity and Intelligence",
            exclusion_group=2,
        )
        item = create_test_item(suffix_mods=[hybrid_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check no Group 2 Intelligence mods are available (excluding Str+Int which is Group 4)
        int_mods = [m for m in available if "Intelligence" in m.stat_text and "Strength" not in m.stat_text]
        assert len(int_mods) == 0, f"Found {len(int_mods)} Intelligence mods, expected 0"


# ============================================================================
# TESTS: Group 3 - Skill Level Mods
# ============================================================================

@pytest.mark.unit
class TestGroup3SkillLevelExclusion:
    """Test Group 3: All skill level modifiers cannot coexist."""

    def test_spell_skills_blocks_projectile_skills(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that Spell Skills blocks Projectile Skills."""
        # Create item with Spell Skills
        spell_mod = create_test_modifier(
            "Spell Skills T1",
            ModType.SUFFIX,
            "+1 to Level of all Spell Skills",
            exclusion_group=3,
        )
        item = create_test_item(suffix_mods=[spell_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check no skill level mods are available
        skill_mods = [m for m in available if "to Level of all" in m.stat_text]
        assert len(skill_mods) == 0, f"Found {len(skill_mods)} skill level mods, expected 0"

    def test_melee_skills_blocks_minion_skills(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that Melee Skills blocks Minion Skills."""
        # Create item with Melee Skills
        melee_mod = create_test_modifier(
            "Melee Skills T1",
            ModType.SUFFIX,
            "+1 to Level of all Melee Skills",
            exclusion_group=3,
        )
        item = create_test_item(suffix_mods=[melee_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check no skill level mods are available
        skill_mods = [m for m in available if "to Level of all" in m.stat_text]
        assert len(skill_mods) == 0, f"Found {len(skill_mods)} skill level mods, expected 0"

    def test_all_skills_ulaman_blocks_other_skill_mods(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that +1 to All Skills (Ulaman) blocks other skill mods."""
        # Create item with All Skills
        all_skills_mod = create_test_modifier(
            "All Skills (Ulaman)",
            ModType.SUFFIX,
            "+1 to Level of all Skills",
            exclusion_group=3,
            tags=["ulaman"],
        )
        item = create_test_item(suffix_mods=[all_skills_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check no skill level mods are available
        skill_mods = [m for m in available if "to Level of all" in m.stat_text]
        assert len(skill_mods) == 0, f"Found {len(skill_mods)} skill level mods, expected 0"


# ============================================================================
# TESTS: Group 4 - Strength and Hybrids
# ============================================================================

@pytest.mark.unit
class TestGroup4StrengthExclusion:
    """Test Group 4: Strength and Str hybrid mods cannot coexist."""

    def test_strength_blocks_str_dex_hybrid(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that Strength blocks Str+Dex hybrid."""
        # Create item with Strength
        str_mod = create_test_modifier(
            "Strength T1",
            ModType.SUFFIX,
            "+20 to Strength",
            exclusion_group=4,
        )
        item = create_test_item(suffix_mods=[str_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check no Strength mods are available
        str_mods = [m for m in available if "Strength" in m.stat_text]
        assert len(str_mods) == 0, f"Found {len(str_mods)} Strength mods, expected 0"

    def test_str_dex_hybrid_blocks_str_int_hybrid(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that Str+Dex hybrid blocks Str+Int hybrid."""
        # Create item with Str+Dex hybrid
        str_dex_mod = create_test_modifier(
            "Str+Dex Hybrid",
            ModType.SUFFIX,
            "+(9-15) to Strength and Dexterity",
            exclusion_group=4,
        )
        item = create_test_item(suffix_mods=[str_dex_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check no Strength mods are available
        str_mods = [m for m in available if "Strength" in m.stat_text]
        assert len(str_mods) == 0, f"Found {len(str_mods)} Strength mods, expected 0"


# ============================================================================
# TESTS: Cross-Group Non-Exclusion
# ============================================================================

@pytest.mark.unit
class TestCrossGroupNonExclusion:
    """Test that mods from different exclusion groups can coexist."""

    def test_dexterity_and_intelligence_can_coexist(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that Dexterity (Group 1) and Intelligence (Group 2) can coexist."""
        # Create item with Dexterity (Group 1)
        dex_mod = create_test_modifier(
            "Dexterity T1",
            ModType.SUFFIX,
            "+20 to Dexterity",
            exclusion_group=1,
        )
        item = create_test_item(suffix_mods=[dex_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check that Intelligence mods ARE available (different group)
        int_mods = [m for m in available if "Intelligence" in m.stat_text and "Dexterity" not in m.stat_text]
        assert len(int_mods) > 0, "Intelligence mods should be available (different exclusion group)"

    def test_skill_level_and_attributes_can_coexist(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that Skill Level mods (Group 3) and Attribute mods (Groups 1,2,4) can coexist."""
        # Create item with Spell Skills (Group 3)
        spell_mod = create_test_modifier(
            "Spell Skills T1",
            ModType.SUFFIX,
            "+1 to Level of all Spell Skills",
            exclusion_group=3,
        )
        item = create_test_item(suffix_mods=[spell_mod])

        # Get available suffixes
        available = modifier_pool_with_exclusions.get_all_mods_for_category(
            "amulet",
            "suffix",
            item
        )

        # Check that Strength mods ARE available (different group)
        str_mods = [m for m in available if "Strength" in m.stat_text]
        assert len(str_mods) > 0, "Strength mods should be available (different exclusion group)"


# ============================================================================
# TESTS: Modifier Pool Integration
# ============================================================================

@pytest.mark.unit
class TestModifierPoolExclusionIntegration:
    """Test exclusion group filtering in modifier pool methods."""

    def test_get_excluded_exclusion_groups_from_item(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that excluded exclusion groups are correctly extracted from item."""
        # Create item with mods from groups 1 and 3
        dex_mod = create_test_modifier(
            "Dexterity T1",
            ModType.SUFFIX,
            "+20 to Dexterity",
            exclusion_group=1,
        )
        spell_mod = create_test_modifier(
            "Spell Skills T1",
            ModType.SUFFIX,
            "+1 to Level of all Spell Skills",
            exclusion_group=3,
        )
        item = create_test_item(suffix_mods=[dex_mod, spell_mod])

        # Get excluded groups
        excluded = modifier_pool_with_exclusions._get_excluded_exclusion_groups_from_item(item)

        assert 1 in excluded, "Group 1 should be excluded"
        assert 3 in excluded, "Group 3 should be excluded"
        assert 2 not in excluded, "Group 2 should not be excluded"
        assert 4 not in excluded, "Group 4 should not be excluded"

    def test_filter_eligible_mods_respects_exclusion_groups(
        self,
        modifier_pool_with_exclusions,
        create_test_item,
        create_test_modifier
    ):
        """Test that _filter_eligible_mods correctly filters by exclusion groups."""
        # Create item with Group 3 mod
        spell_mod = create_test_modifier(
            "Spell Skills T1",
            ModType.SUFFIX,
            "+1 to Level of all Spell Skills",
            exclusion_group=3,
        )
        item = create_test_item(suffix_mods=[spell_mod])

        # Filter suffixes
        pool = modifier_pool_with_exclusions._suffix_pool
        eligible = modifier_pool_with_exclusions._filter_eligible_mods(
            pool,
            "amulet",
            82,
            [],  # excluded_groups
            item=item
        )

        # Check that no Group 3 mods are eligible
        group_3_mods = [m for m in eligible if m.exclusion_group == 3]
        assert len(group_3_mods) == 0, "No Group 3 mods should be eligible"
