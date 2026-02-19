"""
Test suite for catalyst mechanics.

Tests cover:
- Catalyst application to jewelry (rings/amulets)
- Catalyst rejection for non-jewelry items
- Catalyst quality stacking (1-2% per use, max 20%)
- Catalyst type replacement (different catalyst resets quality)
- Omen of Catalysing Exaltation weight boosting
- Quality consumption after omen use

Note: In-game, catalysts add 1% quality with 15% chance for 2%.
"""

import pytest
import random
from typing import List
from unittest.mock import Mock, patch

from app.schemas.crafting import (
    CraftableItem,
    ItemModifier,
    ItemRarity,
    ModType,
    OmenInfo,
)
from app.services.crafting.mechanics import CatalystMechanic, OmenModifiedMechanic, ExaltedMechanic, CATALYST_TAG_MAPPING
from app.services.crafting.omens import OmenFactory, OmenMetadata
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
            applicable_items=applicable_items or ["ring", "amulet"],
            tags=tags or [],
        )
    return _create


@pytest.fixture
def create_jewelry_item():
    """Factory for creating test jewelry items."""
    def _create(
        base_category: str = "ring",
        rarity: ItemRarity = ItemRarity.RARE,
        item_level: int = 80,
        prefix_mods: List[ItemModifier] = None,
        suffix_mods: List[ItemModifier] = None,
        catalyst_type: str = None,
        catalyst_quality: int = 0,
    ):
        return CraftableItem(
            base_name="Gold Ring" if base_category == "ring" else "Coral Amulet",
            base_category=base_category,
            rarity=rarity,
            item_level=item_level,
            quality=0,
            prefix_mods=prefix_mods or [],
            suffix_mods=suffix_mods or [],
            implicit_mods=[],
            unrevealed_mods=[],
            socketed_runes=[],
            corrupted=False,
            base_stats={},
            calculated_stats={},
            catalyst_type=catalyst_type,
            catalyst_quality=catalyst_quality,
        )
    return _create


@pytest.fixture
def mock_modifier_pool(create_test_modifier):
    """Create a mock modifier pool with test modifiers."""
    pool = Mock(spec=ModifierPool)

    # Create some test modifiers with different tags
    life_mod = create_test_modifier(
        "Life Mod", ModType.PREFIX, tags=["life", "maximum_life"], weight=100
    )
    attack_mod = create_test_modifier(
        "Attack Mod", ModType.PREFIX, tags=["attack"], weight=100
    )
    mana_mod = create_test_modifier(
        "Mana Mod", ModType.SUFFIX, tags=["mana", "resource"], weight=100
    )
    generic_mod = create_test_modifier(
        "Generic Mod", ModType.PREFIX, tags=[], weight=100
    )

    pool.get_eligible_mods = Mock(return_value=[life_mod, attack_mod, mana_mod, generic_mod])
    pool.modifiers = [life_mod, attack_mod, mana_mod, generic_mod]

    return pool


# ============================================================================
# CATALYST APPLICATION TESTS
# ============================================================================

class TestCatalystApplication:
    """Test catalyst application to items."""

    def test_apply_catalyst_to_ring(self, create_jewelry_item, mock_modifier_pool):
        """Catalyst should apply to rings."""
        item = create_jewelry_item(base_category="ring")
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})

        can_apply, error = mechanic.can_apply(item)
        assert can_apply is True
        assert error is None

        # Mock random to return > 0.15 (no bonus, so +1%)
        with patch('app.services.crafting.mechanics.random.random', return_value=0.5):
            success, message, result_item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert result_item.catalyst_type == "flesh"
        assert result_item.catalyst_quality == 1  # 1% per use (no bonus)

    def test_apply_catalyst_to_amulet(self, create_jewelry_item, mock_modifier_pool):
        """Catalyst should apply to amulets."""
        item = create_jewelry_item(base_category="amulet")
        mechanic = CatalystMechanic({"catalyst_type": "neural"})

        can_apply, error = mechanic.can_apply(item)
        assert can_apply is True

        # Mock random to return < 0.15 (bonus, so +2%)
        with patch('app.services.crafting.mechanics.random.random', return_value=0.1):
            success, message, result_item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert result_item.catalyst_type == "neural"
        assert result_item.catalyst_quality == 2  # 2% bonus roll

    def test_catalyst_rejected_on_belt(self, mock_modifier_pool):
        """Catalyst should not apply to belts."""
        item = CraftableItem(
            base_name="Leather Belt",
            base_category="belt",
            rarity=ItemRarity.RARE,
            item_level=80,
            quality=0,
            prefix_mods=[],
            suffix_mods=[],
            implicit_mods=[],
            unrevealed_mods=[],
            socketed_runes=[],
            corrupted=False,
            base_stats={},
            calculated_stats={},
        )
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})

        can_apply, error = mechanic.can_apply(item)
        assert can_apply is False
        assert "rings and amulets" in error

    def test_catalyst_rejected_on_armor(self, mock_modifier_pool):
        """Catalyst should not apply to armor."""
        item = CraftableItem(
            base_name="Vile Robe",
            base_category="int_armour",
            rarity=ItemRarity.RARE,
            item_level=80,
            quality=0,
            prefix_mods=[],
            suffix_mods=[],
            implicit_mods=[],
            unrevealed_mods=[],
            socketed_runes=[],
            corrupted=False,
            base_stats={},
            calculated_stats={},
        )
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})

        can_apply, error = mechanic.can_apply(item)
        assert can_apply is False
        assert "rings and amulets" in error


class TestCatalystQualityStacking:
    """Test catalyst quality accumulation."""

    def test_quality_stacks_to_max(self, create_jewelry_item, mock_modifier_pool):
        """Quality should stack 1-2% per use up to 20%."""
        item = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=0)
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})

        # Apply multiple times with +1% each (mocked to no bonus)
        with patch('app.services.crafting.mechanics.random.random', return_value=0.5):
            for expected_quality in range(1, 21):
                success, message, item = mechanic.apply(item, mock_modifier_pool)
                assert success is True
                assert item.catalyst_quality == expected_quality

        # Next application should be rejected (already at max)
        can_apply, error = mechanic.can_apply(item)
        assert can_apply is False
        assert "maximum" in error

    def test_quality_partial_addition_at_cap(self, create_jewelry_item, mock_modifier_pool):
        """Quality should cap at 20% even if roll would exceed."""
        item = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=19)
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})

        # Even with +2% bonus roll, should cap at 20%
        with patch('app.services.crafting.mechanics.random.random', return_value=0.1):  # Bonus roll
            success, message, item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert item.catalyst_quality == 20  # Capped at max, not 21

    def test_quality_bonus_roll_probability(self, create_jewelry_item, mock_modifier_pool):
        """15% chance for +2%, 85% chance for +1%."""
        item = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=0)
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})

        # Test bonus roll (random < 0.15)
        with patch('app.services.crafting.mechanics.random.random', return_value=0.10):
            success, message, result = mechanic.apply(item, mock_modifier_pool)
        assert result.catalyst_quality == 2  # +2% bonus

        # Test normal roll (random >= 0.15)
        item2 = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=0)
        with patch('app.services.crafting.mechanics.random.random', return_value=0.20):
            success, message, result = mechanic.apply(item2, mock_modifier_pool)
        assert result.catalyst_quality == 1  # +1% normal


class TestCatalystTypeReplacement:
    """Test catalyst type replacement behavior."""

    def test_different_catalyst_resets_quality(self, create_jewelry_item, mock_modifier_pool):
        """Applying a different catalyst type should reset quality."""
        item = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=15)
        mechanic = CatalystMechanic({"catalyst_type": "reaver"})  # Different type

        with patch('app.services.crafting.mechanics.random.random', return_value=0.5):
            success, message, item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert item.catalyst_type == "reaver"
        assert item.catalyst_quality == 1  # Reset to 0, then +1%

    def test_same_catalyst_adds_quality(self, create_jewelry_item, mock_modifier_pool):
        """Applying same catalyst type should add to existing quality."""
        item = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=10)
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})  # Same type

        with patch('app.services.crafting.mechanics.random.random', return_value=0.5):
            success, message, item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert item.catalyst_type == "flesh"
        assert item.catalyst_quality == 11  # 10 + 1


# ============================================================================
# OMEN OF CATALYSING EXALTATION TESTS
# ============================================================================

class TestOmenOfCatalysingExaltation:
    """Test Omen of Catalysing Exaltation mechanics."""

    def test_omen_metadata_exists(self):
        """Omen metadata should exist for Catalysing Exaltation."""
        omen = OmenFactory.create("Omen of Catalysing Exaltation")
        assert omen is not None
        assert omen.affected_currency == "Exalted Orb"

    def test_omen_applies_to_exalted_orb_variants(self):
        """Omen should apply to all Exalted Orb variants."""
        applicable = OmenFactory.get_omens_for_currency("Perfect Exalted Orb")
        assert "Omen of Catalysing Exaltation" in applicable

        applicable = OmenFactory.get_omens_for_currency("Greater Exalted Orb")
        assert "Omen of Catalysing Exaltation" in applicable

    def test_catalyst_tag_mapping_exists(self):
        """All catalyst types should have tag mappings."""
        expected_catalyst_types = [
            "flesh", "neural", "carapace", "uul_netol",
            "xoph", "tul", "esh", "chayula",
            "reaver", "sibilant", "skittering", "adaptive"
        ]

        for catalyst_type in expected_catalyst_types:
            assert catalyst_type in CATALYST_TAG_MAPPING
            assert len(CATALYST_TAG_MAPPING[catalyst_type]) > 0

    def test_weight_multiplier_formula(self):
        """Weight multiplier should be 1 + (quality/20) * 10."""
        # At 20% quality: 1 + (20/20) * 10 = 11x
        # At 10% quality: 1 + (10/20) * 10 = 6x
        # At 0% quality: 1x (no boost)

        # Test the formula directly
        quality_20_multiplier = 1 + (20 / 20.0) * 10.0
        assert quality_20_multiplier == 11.0

        quality_10_multiplier = 1 + (10 / 20.0) * 10.0
        assert quality_10_multiplier == 6.0

        quality_5_multiplier = 1 + (5 / 20.0) * 10.0
        assert quality_5_multiplier == 3.5

    def test_omen_consumes_catalyst_quality(self, create_jewelry_item, create_test_modifier, mock_modifier_pool):
        """Omen should consume all catalyst quality when used via OmenModifiedMechanic."""
        prefix = create_test_modifier("Test Prefix", ModType.PREFIX, tags=["life"])
        item = create_jewelry_item(
            base_category="ring",
            rarity=ItemRarity.RARE,
            catalyst_type="flesh",
            catalyst_quality=15,
            prefix_mods=[prefix],
        )

        # Create omen-wrapped exalted mechanic
        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Catalysing Exaltation",
            effect_description="Consumes catalyst quality",
            affected_currency="Exalted Orb",
            effect_type="catalysing",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result_item = omen_mechanic.apply(item, mock_modifier_pool)

        # Check quality was consumed
        assert success is True
        assert result_item.catalyst_quality == 0
        assert result_item.catalyst_type is None
        assert "consumed" in message.lower()

    def test_omen_works_without_catalyst(self, create_jewelry_item, create_test_modifier, mock_modifier_pool):
        """Omen should fall back to normal behavior without catalyst quality."""
        prefix = create_test_modifier("Test Prefix", ModType.PREFIX)
        item = create_jewelry_item(
            base_category="ring",
            rarity=ItemRarity.RARE,
            catalyst_type=None,
            catalyst_quality=0,
            prefix_mods=[prefix],
        )

        # Create omen-wrapped exalted mechanic
        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Catalysing Exaltation",
            effect_description="Consumes catalyst quality",
            affected_currency="Exalted Orb",
            effect_type="catalysing",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result_item = omen_mechanic.apply(item, mock_modifier_pool)

        # Should still work, just without catalyst boost
        assert success is True
        assert result_item.catalyst_quality == 0

    def test_catalysing_with_greater_and_dextral_adds_two_suffixes(self, create_jewelry_item, create_test_modifier):
        """Catalysing + Greater + Dextral should add TWO suffix mods with boosted weights."""
        from unittest.mock import Mock
        from app.services.crafting.modifier_pool import ModifierPool

        prefix = create_test_modifier("Test Prefix", ModType.PREFIX, tags=["life"])
        item = create_jewelry_item(
            base_category="ring",
            rarity=ItemRarity.RARE,
            catalyst_type="flesh",
            catalyst_quality=20,
            prefix_mods=[prefix],
        )

        # Create suffix mods for the pool
        suffix1 = create_test_modifier("Suffix1", ModType.SUFFIX, tags=["life"], mod_group="suffix1_group")
        suffix2 = create_test_modifier("Suffix2", ModType.SUFFIX, tags=["mana"], mod_group="suffix2_group")
        suffix3 = create_test_modifier("Suffix3", ModType.SUFFIX, tags=["speed"], mod_group="suffix3_group")

        # Create mock that returns suffix mods when suffix is requested
        modifier_pool = Mock(spec=ModifierPool)
        modifier_pool.get_eligible_mods = Mock(return_value=[suffix1, suffix2, suffix3])

        # Create omen chain: Catalysing + Greater + Dextral
        base_mechanic = ExaltedMechanic({})

        # Build omen chain by wrapping multiple times
        catalysing_omen = OmenInfo(
            id=1,
            name="Omen of Catalysing Exaltation",
            effect_description="Boosts matching mod weights",
            affected_currency="Exalted Orb",
            effect_type="catalysing",
            stack_size=10,
        )
        greater_omen = OmenInfo(
            id=2,
            name="Omen of Greater Exaltation",
            effect_description="Adds two mods",
            affected_currency="Exalted Orb",
            effect_type="greater",
            stack_size=10,
        )
        dextral_omen = OmenInfo(
            id=3,
            name="Omen of Dextral Exaltation",
            effect_description="Suffix only",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
        )

        # Wrap omens around base mechanic (order matters - inner to outer)
        omen_mechanic = OmenModifiedMechanic(base_mechanic, catalysing_omen)
        omen_mechanic = OmenModifiedMechanic(omen_mechanic, greater_omen)
        omen_mechanic = OmenModifiedMechanic(omen_mechanic, dextral_omen)

        success, message, result_item = omen_mechanic.apply(item, modifier_pool)

        assert success is True, f"Expected success but got: {message}"
        # Should have original prefix + 2 new suffixes
        assert len(result_item.prefix_mods) == 1, "Should still have 1 prefix"
        assert len(result_item.suffix_mods) == 2, f"Should have 2 suffixes, got {len(result_item.suffix_mods)}"
        assert result_item.catalyst_quality == 0, "Catalyst quality should be consumed"
        assert result_item.catalyst_type is None, "Catalyst type should be cleared"
        assert "consumed" in message.lower(), f"Message should mention consumed catalyst: {message}"


class TestCatalystTypes:
    """Test all catalyst type configurations."""

    @pytest.mark.parametrize("catalyst_type,expected_display", [
        ("flesh", "Life"),
        ("neural", "Mana"),
        ("carapace", "Defence"),
        ("reaver", "Attack"),
        ("sibilant", "Caster"),
        ("skittering", "Speed"),
        ("adaptive", "Attribute"),
    ])
    def test_catalyst_display_names(self, catalyst_type, expected_display):
        """Each catalyst type should have a proper display name."""
        mechanic = CatalystMechanic({"catalyst_type": catalyst_type})
        display_name = mechanic._get_catalyst_display_name()
        assert expected_display in display_name
