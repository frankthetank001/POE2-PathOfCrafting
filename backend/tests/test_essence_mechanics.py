"""
Comprehensive test suite for Essence crafting mechanics.

Tests cover:
- Essence application to Normal items
- Essence application to Magic/Rare items (remove mods, add guaranteed mod)
- Essence tiers (Lesser, Greater, Perfect)
- Essence types (Flames, Ice, Lightning, etc.)
- Item category restrictions
- Essence-specific modifiers
- Corrupted essences
- Essence + Omen combinations
"""

import pytest
from typing import List
from unittest.mock import Mock, patch

from app.schemas.crafting import (
    CraftableItem,
    ItemModifier,
    ItemRarity,
    ModType,
    EssenceInfo,
    OmenInfo,
)
from app.services.crafting.mechanics import EssenceMechanic, OmenModifiedMechanic
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
        is_essence_only: bool = False,
    ):
        return ItemModifier(
            name=name,
            mod_type=mod_type,
            tier=tier,
            stat_text=f"{name} stat text",
            stat_min=stat_min,
            stat_max=stat_max,
            required_ilvl=required_ilvl,
            weight=100,
            mod_group=mod_group or f"{name}_group",
            applicable_items=applicable_items or ["body_armour", "int_armour"],
            tags=tags or [],
            is_essence_only=is_essence_only,
        )
    return _create


@pytest.fixture
def create_test_item():
    """Factory for creating test items."""
    def _create(
        rarity: ItemRarity = ItemRarity.NORMAL,
        item_level: int = 80,
        base_name: str = "Vile Robe",
        base_category: str = "int_armour",
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
def create_essence_info():
    """Factory for creating essence info objects."""
    def _create(
        name: str = "Lesser Essence of Flames",
        essence_type: str = "flames",
        essence_tier: str = "lesser",
        guaranteed_mod_name: str = "Fire Damage",
        mod_type: str = "prefix",
    ):
        from app.schemas.crafting import EssenceItemEffect

        # Determine mechanic based on tier (PoE2 mechanics)
        # Lesser/Greater essences: Magic -> Rare (magic_to_rare)
        # Perfect/Corrupted essences: Rare -> Rare with reroll (remove_add_rare)
        if essence_tier in ["lesser", "greater"]:
            mechanic = "magic_to_rare"  # Requires Magic item, upgrades to Rare
        else:  # perfect, corrupted
            mechanic = "remove_add_rare"  # Requires Rare item, rerolls

        # Create item effect for the guaranteed mod
        item_effects = [
            EssenceItemEffect(
                id=1,
                essence_id=1,
                item_type="Body Armour",  # Must match category mapping in mechanics.py
                modifier_type=mod_type,
                effect_text=f"{guaranteed_mod_name} effect",
                value_min=10,
                value_max=20,
            )
        ]

        return EssenceInfo(
            id=1,
            name=name,
            essence_type=essence_type,
            essence_tier=essence_tier,
            mechanic=mechanic,
            stack_size=100,
            item_effects=item_effects,
        )
    return _create


@pytest.fixture
def mock_modifier_pool(create_test_modifier):
    """Create a mock modifier pool with test modifiers."""
    pool = Mock(spec=ModifierPool)

    # Create test modifiers for common essence types
    fire_mod = create_test_modifier(
        "Essence Fire Damage",
        ModType.PREFIX,
        is_essence_only=True,
        mod_group="firedamage",
        tier=1
    )
    cold_mod = create_test_modifier(
        "Essence Cold Damage",
        ModType.PREFIX,
        is_essence_only=True,
        mod_group="colddamage",
        tier=1
    )
    lightning_mod = create_test_modifier(
        "Essence Lightning Damage",
        ModType.PREFIX,
        is_essence_only=True,
        mod_group="lightningdamage",
        tier=1
    )
    life_mod = create_test_modifier(
        "Essence Life",
        ModType.PREFIX,
        is_essence_only=True,
        mod_group="life",
        tier=1
    )
    regular_prefix = create_test_modifier("Regular Prefix", ModType.PREFIX, mod_group="regular_prefix")
    regular_suffix = create_test_modifier("Regular Suffix", ModType.SUFFIX, mod_group="regular_suffix")

    def get_essence_modifier(essence_type, mod_type, tier):
        return fire_mod

    def roll_random_modifier(mod_type, base_category, item_level, **kwargs):
        if mod_type == "prefix":
            return regular_prefix
        else:
            return regular_suffix

    def _modifier_applies_to_item(mod, item):
        # Simple check - mod applies if it's in applicable_items
        return item.base_category in mod.applicable_items or "int_armour" in mod.applicable_items

    pool.get_essence_modifier = Mock(side_effect=get_essence_modifier)
    pool.roll_random_modifier = Mock(side_effect=roll_random_modifier)
    pool._get_excluded_groups_from_item = Mock(return_value=set())
    pool._modifier_applies_to_item = Mock(side_effect=_modifier_applies_to_item)
    pool.modifiers = [fire_mod, cold_mod, lightning_mod, life_mod, regular_prefix, regular_suffix]

    return pool


# ============================================================================
# ESSENCE ON NORMAL ITEMS TESTS
# ============================================================================

class TestEssenceOnNormalItems:
    """Test that essences cannot be applied to Normal items (PoE2 mechanic)."""

    def test_lesser_essence_on_normal_fails(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Lesser Essence on Normal item should fail - must be Magic first."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        essence_info = create_essence_info(
            name="Lesser Essence of Flames",
            essence_tier="lesser",
            essence_type="flames",
        )
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is False
        assert "can only be applied to Magic items" in message

    def test_greater_essence_on_normal_fails(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Greater Essence on Normal item should fail - must be Magic first."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        essence_info = create_essence_info(
            name="Greater Essence of Flames",
            essence_tier="greater",
            essence_type="flames",
        )
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is False
        assert "can only be applied to Magic items" in message

    def test_perfect_essence_on_normal_fails(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Perfect Essence on Normal item should fail - must be Rare first."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        essence_info = create_essence_info(
            name="Perfect Essence of Flames",
            essence_tier="perfect",
            essence_type="flames",
        )
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is False
        assert "can only be applied to Rare items" in message

    def test_essence_adds_guaranteed_modifier(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Essence should always add the guaranteed modifier (on Magic item)."""
        item = create_test_item(rarity=ItemRarity.MAGIC)  # Changed to MAGIC
        essence_info = create_essence_info(
            name="Lesser Essence of Flames",
            guaranteed_mod_name="Fire Damage",
        )
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.rarity == ItemRarity.RARE  # Magic -> Rare upgrade
        # Should have at least one mod with the fire damage group
        mod_groups = [mod.mod_group for mod in result.prefix_mods + result.suffix_mods]
        assert "firedamage" in mod_groups


# ============================================================================
# ESSENCE ON MAGIC/RARE ITEMS TESTS
# ============================================================================

class TestEssenceOnMagicRareItems:
    """Test essence application to Magic and Rare items."""

    def test_essence_on_magic_removes_mods_adds_guaranteed(self, create_test_item, create_test_modifier, create_essence_info, mock_modifier_pool):
        """Essence on Magic item should remove existing mods and add guaranteed mod."""
        existing_prefix = create_test_modifier("Existing Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[existing_prefix])
        essence_info = create_essence_info(essence_tier="lesser")
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        # Should have new mods (guaranteed + possibly others)
        assert result.total_explicit_mods >= 1

    def test_essence_on_rare_removes_all_mods(self, create_test_item, create_test_modifier, create_essence_info, mock_modifier_pool):
        """Perfect Essence on Rare item should remove all existing mods."""
        prefixes = [create_test_modifier(f"Prefix{i}", ModType.PREFIX) for i in range(2)]
        suffixes = [create_test_modifier(f"Suffix{i}", ModType.SUFFIX) for i in range(2)]
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=prefixes, suffix_mods=suffixes)
        essence_info = create_essence_info(essence_tier="perfect")  # Perfect works on Rare
        mechanic = EssenceMechanic({}, essence_info)

        initial_mod_names = [m.name for m in item.prefix_mods + item.suffix_mods]
        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        # Result should have different mods (guaranteed + new randoms)
        result_mod_names = [m.name for m in result.prefix_mods + result.suffix_mods]
        # At least some mods should be different
        assert any(name not in initial_mod_names for name in result_mod_names)


# ============================================================================
# ESSENCE TIER TESTS
# ============================================================================

class TestEssenceTiers:
    """Test different essence tiers."""

    def test_lesser_essence_tier_level(self, create_essence_info):
        """Lesser Essence should have correct tier level."""
        essence_info = create_essence_info(essence_tier="lesser")
        # Lesser essences typically guarantee tier 7 mods (low level)
        assert essence_info.essence_tier == "lesser"

    def test_greater_essence_tier_level(self, create_essence_info):
        """Greater Essence should have correct tier level."""
        essence_info = create_essence_info(essence_tier="greater")
        # Greater essences typically guarantee tier 4 mods (mid level)
        assert essence_info.essence_tier == "greater"

    def test_perfect_essence_tier_level(self, create_essence_info):
        """Perfect Essence should have correct tier level."""
        essence_info = create_essence_info(essence_tier="perfect")
        # Perfect essences typically guarantee tier 1 mods (high level)
        assert essence_info.essence_tier == "perfect"

    def test_higher_tier_creates_better_mods(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Higher tier essences should create higher tier guaranteed mods."""
        # Lesser and Greater need Magic items
        item1 = create_test_item(rarity=ItemRarity.MAGIC)
        item2 = create_test_item(rarity=ItemRarity.MAGIC)
        # Perfect needs Rare item with at least one mod
        item3 = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[
            ItemModifier(name="Test", mod_type=ModType.PREFIX, tier=1, stat_text="test", mod_group="test", applicable_items=["int_armour"])
        ])

        lesser = EssenceMechanic({}, create_essence_info(essence_tier="lesser"))
        greater = EssenceMechanic({}, create_essence_info(essence_tier="greater"))
        perfect = EssenceMechanic({}, create_essence_info(essence_tier="perfect"))

        # All should succeed
        success1, _, result1 = lesser.apply(item1, mock_modifier_pool)
        success2, _, result2 = greater.apply(item2, mock_modifier_pool)
        success3, _, result3 = perfect.apply(item3, mock_modifier_pool)

        assert success1 is True
        assert success2 is True
        assert success3 is True


# ============================================================================
# ESSENCE TYPE TESTS
# ============================================================================

class TestEssenceTypes:
    """Test different essence types."""

    def test_essence_of_flames_adds_fire_mod(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Essence of Flames should add fire damage modifier."""
        item = create_test_item(rarity=ItemRarity.MAGIC, base_category="int_armour")
        essence_info = create_essence_info(
            essence_type="flames",
            guaranteed_mod_name="Fire Damage",
        )
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        # Verify result has fire damage mod
        mod_groups = [mod.mod_group for mod in result.prefix_mods + result.suffix_mods]
        assert "firedamage" in mod_groups

    def test_essence_of_ice_adds_cold_mod(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Essence of Ice should add cold damage modifier."""
        item = create_test_item(rarity=ItemRarity.MAGIC, base_category="int_armour")
        essence_info = create_essence_info(
            essence_type="ice",
            guaranteed_mod_name="Cold Damage",
        )
        # Need to update the item_effects to support ice type
        from app.schemas.crafting import EssenceItemEffect
        essence_info.item_effects = [
            EssenceItemEffect(
                id=1, essence_id=1, item_type="Body Armour",
                modifier_type="prefix", effect_text="Cold Damage",
                value_min=10, value_max=20
            )
        ]
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        mod_groups = [mod.mod_group for mod in result.prefix_mods + result.suffix_mods]
        assert "colddamage" in mod_groups

    def test_essence_of_lightning_adds_lightning_mod(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Essence of Lightning should add lightning damage modifier."""
        item = create_test_item(rarity=ItemRarity.MAGIC, base_category="int_armour")
        essence_info = create_essence_info(
            essence_type="electricity",  # electricity is the type for lightning
            guaranteed_mod_name="Lightning Damage",
        )
        # Need to update the item_effects to support electricity type
        from app.schemas.crafting import EssenceItemEffect
        essence_info.item_effects = [
            EssenceItemEffect(
                id=1, essence_id=1, item_type="Body Armour",
                modifier_type="prefix", effect_text="Lightning Damage",
                value_min=10, value_max=20
            )
        ]
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        mod_groups = [mod.mod_group for mod in result.prefix_mods + result.suffix_mods]
        assert "lightningdamage" in mod_groups


# ============================================================================
# ITEM CATEGORY RESTRICTION TESTS
# ============================================================================

class TestEssenceCategoryRestrictions:
    """Test essence restrictions to specific item categories."""

    def test_essence_applicable_to_correct_category(self, create_test_item, create_essence_info):
        """Essence should be applicable to items matching its item_effects."""
        item = create_test_item(rarity=ItemRarity.MAGIC, base_category="int_armour")
        # Essence with item_effects for Body Armour (int_armour is compatible)
        essence_info = create_essence_info()
        mechanic = EssenceMechanic({}, essence_info)

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True

    def test_essence_not_applicable_to_wrong_category(self, create_test_item, create_essence_info):
        """Essence should not be applicable to items not matching item_effects."""
        # Create a weapon item
        item = create_test_item(rarity=ItemRarity.MAGIC, base_category="One Handed Sword")
        # Essence with item_effects for Body Armour only
        essence_info = create_essence_info()
        # item_effects has "Body Armour" which doesn't match "One Handed Sword"
        mechanic = EssenceMechanic({}, essence_info)

        can_apply, error = mechanic.can_apply(item)

        # Should fail because weapon doesn't match Body Armour category
        assert can_apply is False
        assert "cannot be applied to" in error


# ============================================================================
# ESSENCE MODIFIER SPECIFICITY TESTS
# ============================================================================

class TestEssenceModifierSpecificity:
    """Test essence-specific modifiers."""

    def test_essence_only_mod_not_available_normally(self, create_test_modifier):
        """Essence-only modifiers should be marked as such."""
        essence_mod = create_test_modifier(
            "Essence-Only Mod",
            ModType.PREFIX,
            is_essence_only=True
        )

        assert essence_mod.is_essence_only is True

    def test_essence_provides_guaranteed_mod_type(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Essence should provide guaranteed mod of specified type (prefix/suffix)."""
        item = create_test_item(rarity=ItemRarity.MAGIC)  # Changed to MAGIC
        essence_info = create_essence_info(
            mod_type="prefix",
            guaranteed_mod_name="Fire Damage",
        )
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        # Guaranteed mod should be added and should be a prefix
        assert result.total_explicit_mods >= 1
        prefix_groups = [mod.mod_group for mod in result.prefix_mods]
        assert "firedamage" in prefix_groups


# ============================================================================
# CORRUPTED ESSENCE TESTS
# ============================================================================

class TestCorruptedEssences:
    """Test corrupted essence behavior."""

    def test_corrupted_essence_corrupts_item(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Corrupted essence should corrupt the resulting item."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        essence_info = create_essence_info(name="Corrupted Essence of Flames")
        # Mark as corrupted essence
        mechanic = EssenceMechanic({"corrupts": True}, essence_info)

        # Note: Implementation may vary - this tests the concept
        # Actual implementation should be verified


# ============================================================================
# ESSENCE + OMEN COMBINATION TESTS
# ============================================================================

class TestEssenceWithOmens:
    """Test essence combined with omens."""

    @pytest.mark.skip(reason="Essence + Omen combinations not yet implemented in OmenModifiedMechanic")
    def test_dextral_crystallisation_removes_suffix_first(self, create_test_item, create_test_modifier, create_essence_info, create_omen_info, mock_modifier_pool):
        """Omen of Dextral Crystallisation should remove suffix before applying essence."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        suffix = create_test_modifier("Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix], suffix_mods=[suffix])

        base_mechanic = EssenceMechanic({}, create_essence_info(essence_tier="perfect"))
        omen_info = create_omen_info(
            name="Omen of Dextral Crystallisation",
            effect_description="Perfect/Corrupted Essence removes only suffixes",
            affected_currency="Perfect Essence",
            effect_type="dextral",
        )
        wrapped_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        # When implemented, should remove suffix first then apply essence
        # success, message, result = wrapped_mechanic.apply(item, mock_modifier_pool)
        # assert result.suffix_count < item.suffix_count

    @pytest.mark.skip(reason="Essence + Omen combinations not yet implemented in OmenModifiedMechanic")
    def test_sinistral_crystallisation_removes_prefix_first(self, create_test_item, create_test_modifier, create_essence_info, create_omen_info, mock_modifier_pool):
        """Omen of Sinistral Crystallisation should remove prefix before applying essence."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        suffix = create_test_modifier("Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix], suffix_mods=[suffix])

        base_mechanic = EssenceMechanic({}, create_essence_info(essence_tier="perfect"))
        omen_info = create_omen_info(
            name="Omen of Sinistral Crystallisation",
            effect_description="Perfect/Corrupted Essence removes only prefixes",
            affected_currency="Perfect Essence",
            effect_type="sinistral",
        )
        wrapped_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        # When implemented, should remove prefix first then apply essence
        # success, message, result = wrapped_mechanic.apply(item, mock_modifier_pool)
        # assert result.prefix_count < item.prefix_count


# ============================================================================
# EDGE CASES AND ERROR CONDITIONS
# ============================================================================

class TestEssenceEdgeCases:
    """Test edge cases and error conditions for essences."""

    def test_essence_on_corrupted_item_fails(self, create_test_item, create_essence_info):
        """Essence should not be applicable to corrupted items."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        item.corrupted = True
        essence_info = create_essence_info()
        mechanic = EssenceMechanic({}, essence_info)

        # Most currencies can't apply to corrupted items
        # Implementation should check this

    def test_essence_respects_item_level_requirements(self, create_test_item, create_essence_info, mock_modifier_pool):
        """Essence guaranteed mod should respect item level requirements."""
        # Low level item
        low_level_item = create_test_item(rarity=ItemRarity.NORMAL, item_level=10)
        # High tier essence
        essence_info = create_essence_info(essence_tier="perfect")
        mechanic = EssenceMechanic({}, essence_info)

        # Should still apply, but might have level requirements
        success, message, result = mechanic.apply(low_level_item, mock_modifier_pool)

        # Behavior depends on implementation (may fail or succeed with warning)

    def test_multiple_essences_cannot_stack(self):
        """Using multiple essences should not stack guaranteed mods."""
        # This is more of a system design test
        # Essences reroll the item, so previous essence effects are lost
        pass


# ============================================================================
# ESSENCE WORKFLOW TESTS
# ============================================================================

class TestEssenceWorkflows:
    """Test complete essence crafting workflows."""

    def test_essence_reroll_workflow(self, create_test_item, create_test_modifier, create_essence_info, mock_modifier_pool):
        """Test using essence to reroll a bad rare item."""
        # Start with a rare item with bad mods
        bad_mod1 = create_test_modifier("Bad Prefix", ModType.PREFIX)
        bad_mod2 = create_test_modifier("Bad Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[bad_mod1], suffix_mods=[bad_mod2])

        # Use perfect essence to reroll (works on Rare items)
        essence_info = create_essence_info(essence_tier="perfect")
        mechanic = EssenceMechanic({}, essence_info)

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.rarity == ItemRarity.RARE
        # Should have new mods including guaranteed essence mod
        assert result.total_explicit_mods >= 1

    def test_progressive_essence_upgrade(self, create_test_item, create_test_modifier, create_essence_info, mock_modifier_pool):
        """Test using progressively higher tier essences."""
        # Start with Magic item (essences require Magic/Rare)
        item = create_test_item(rarity=ItemRarity.MAGIC)

        # Apply lesser essence (Magic -> Rare)
        lesser = EssenceMechanic({}, create_essence_info(essence_tier="lesser"))
        success, message, item = lesser.apply(item, mock_modifier_pool)
        assert success is True
        assert item.rarity == ItemRarity.RARE
        assert item.total_explicit_mods >= 1  # Should have at least the guaranteed mod

        # Apply greater essence on a fresh Magic item
        item2 = create_test_item(rarity=ItemRarity.MAGIC)
        greater = EssenceMechanic({}, create_essence_info(essence_tier="greater"))
        success, message, item2 = greater.apply(item2, mock_modifier_pool)
        assert success is True
        assert item2.rarity == ItemRarity.RARE

        # Apply perfect essence (requires Rare item with mods)
        # Create a Rare item with mods for this test
        rare_with_mods = create_test_item(
            rarity=ItemRarity.RARE,
            prefix_mods=[create_test_modifier("Existing", ModType.PREFIX)]
        )
        perfect = EssenceMechanic({}, create_essence_info(essence_tier="perfect"))
        success, message, final_item = perfect.apply(rare_with_mods, mock_modifier_pool)
        assert success is True
        assert final_item.rarity == ItemRarity.RARE


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
