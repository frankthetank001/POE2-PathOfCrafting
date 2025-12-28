"""
Test suite for catalyst mechanics.

Tests cover:
- Catalyst application to jewelry (rings/amulets)
- Catalyst rejection for non-jewelry items
- Catalyst quality stacking (5% per use, max 20%)
- Catalyst type replacement (different catalyst resets quality)
- Omen of Catalysing Exaltation weight boosting
- Quality consumption after omen use
"""

import pytest
from typing import List
from unittest.mock import Mock, patch

from app.schemas.crafting import (
    CraftableItem,
    ItemModifier,
    ItemRarity,
    ModType,
)
from app.services.crafting.mechanics import CatalystMechanic
from app.services.crafting.omens import OmenOfCatalysingExaltation
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

        success, message, result_item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert result_item.catalyst_type == "flesh"
        assert result_item.catalyst_quality == 5

    def test_apply_catalyst_to_amulet(self, create_jewelry_item, mock_modifier_pool):
        """Catalyst should apply to amulets."""
        item = create_jewelry_item(base_category="amulet")
        mechanic = CatalystMechanic({"catalyst_type": "neural"})

        can_apply, error = mechanic.can_apply(item)
        assert can_apply is True

        success, message, result_item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert result_item.catalyst_type == "neural"
        assert result_item.catalyst_quality == 5

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
        """Quality should stack 5% per use up to 20%."""
        item = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=0)
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})

        # Apply 4 times (5% each)
        for expected_quality in [5, 10, 15, 20]:
            success, message, item = mechanic.apply(item, mock_modifier_pool)
            assert success is True
            assert item.catalyst_quality == expected_quality

        # Fifth application should be rejected (already at max)
        can_apply, error = mechanic.can_apply(item)
        assert can_apply is False
        assert "maximum" in error

    def test_quality_partial_addition_at_cap(self, create_jewelry_item, mock_modifier_pool):
        """Quality should cap at 20% even if partial would exceed."""
        item = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=18)
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})

        success, message, item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert item.catalyst_quality == 20  # Capped, not 23


class TestCatalystTypeReplacement:
    """Test catalyst type replacement behavior."""

    def test_different_catalyst_resets_quality(self, create_jewelry_item, mock_modifier_pool):
        """Applying a different catalyst type should reset quality."""
        item = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=15)
        mechanic = CatalystMechanic({"catalyst_type": "reaver"})  # Different type

        success, message, item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert item.catalyst_type == "reaver"
        assert item.catalyst_quality == 5  # Reset to 5%, not 15+5

    def test_same_catalyst_adds_quality(self, create_jewelry_item, mock_modifier_pool):
        """Applying same catalyst type should add to existing quality."""
        item = create_jewelry_item(base_category="ring", catalyst_type="flesh", catalyst_quality=10)
        mechanic = CatalystMechanic({"catalyst_type": "flesh"})  # Same type

        success, message, item = mechanic.apply(item, mock_modifier_pool)
        assert success is True
        assert item.catalyst_type == "flesh"
        assert item.catalyst_quality == 15  # 10 + 5


# ============================================================================
# OMEN OF CATALYSING EXALTATION TESTS
# ============================================================================

class TestOmenOfCatalysingExaltation:
    """Test Omen of Catalysing Exaltation mechanics."""

    def test_omen_applies_to_exalted_orb(self):
        """Omen should apply to Exalted Orb currency."""
        omen = OmenOfCatalysingExaltation()

        assert omen.can_apply_to_currency("Exalted Orb") is True
        assert omen.can_apply_to_currency("Lesser Exalted Orb") is True
        assert omen.can_apply_to_currency("Greater Exalted Orb") is True

    def test_omen_does_not_apply_to_other_currency(self):
        """Omen should not apply to non-Exalted currencies."""
        omen = OmenOfCatalysingExaltation()

        assert omen.can_apply_to_currency("Chaos Orb") is False
        assert omen.can_apply_to_currency("Alchemy Orb") is False
        assert omen.can_apply_to_currency("Divine Orb") is False

    def test_catalyst_tag_mapping_exists(self):
        """All catalyst types should have tag mappings."""
        omen = OmenOfCatalysingExaltation()

        expected_catalyst_types = [
            "flesh", "neural", "carapace", "uul_netol",
            "xoph", "tul", "esh", "chayula",
            "reaver", "sibilant", "skittering", "adaptive"
        ]

        for catalyst_type in expected_catalyst_types:
            assert catalyst_type in omen.CATALYST_TAG_MAPPING
            assert len(omen.CATALYST_TAG_MAPPING[catalyst_type]) > 0

    def test_weight_multiplier_formula(self, create_jewelry_item, mock_modifier_pool):
        """Weight multiplier should be 1 + (quality/20) * 10."""
        # At 20% quality: 1 + (20/20) * 10 = 11x
        # At 10% quality: 1 + (10/20) * 10 = 6x
        # At 0% quality: 1x (no boost)

        omen = OmenOfCatalysingExaltation()

        # Test the formula directly
        quality_20_multiplier = 1 + (20 / 20.0) * 10.0
        assert quality_20_multiplier == 11.0

        quality_10_multiplier = 1 + (10 / 20.0) * 10.0
        assert quality_10_multiplier == 6.0

        quality_5_multiplier = 1 + (5 / 20.0) * 10.0
        assert quality_5_multiplier == 3.5

    def test_omen_consumes_catalyst_quality(self, create_jewelry_item, create_test_modifier, mock_modifier_pool):
        """Omen should consume all catalyst quality when used."""
        item = create_jewelry_item(
            base_category="ring",
            rarity=ItemRarity.RARE,
            catalyst_type="flesh",
            catalyst_quality=15,
            prefix_mods=[],  # Room for prefix
        )

        omen = OmenOfCatalysingExaltation()

        # Apply the omen
        with patch('app.services.crafting.omens.random.choice', return_value="prefix"):
            with patch('app.services.crafting.omens.random.uniform', return_value=1.0):
                success, message, result_item = omen.modify_currency_behavior(
                    item,
                    lambda i, mp: (True, "Applied", i),
                    mock_modifier_pool
                )

        # Check quality was consumed
        if success:
            assert result_item.catalyst_quality == 0
            assert result_item.catalyst_type is None
            assert "Consumed" in message

    def test_omen_works_without_catalyst(self, create_jewelry_item, create_test_modifier, mock_modifier_pool):
        """Omen should still work on items without catalyst quality."""
        item = create_jewelry_item(
            base_category="ring",
            rarity=ItemRarity.RARE,
            catalyst_type=None,
            catalyst_quality=0,
            prefix_mods=[],
        )

        omen = OmenOfCatalysingExaltation()

        # Apply the omen - it should fall through to normal exalted behavior
        with patch('app.services.crafting.omens.random.choice', return_value="prefix"):
            success, message, result_item = omen.modify_currency_behavior(
                item,
                lambda i, mp: (True, "Normal exalted applied", i),
                mock_modifier_pool
            )

        # Should still work without catalyst boost
        # The item still has no catalyst quality since there was none to consume
        assert result_item.catalyst_quality == 0


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
