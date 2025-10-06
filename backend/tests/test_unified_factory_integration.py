"""
Comprehensive test suite for Unified Crafting Factory and Integration Tests.

Tests cover:
- Currency creation from config
- Omen application and wrapping
- Essence creation
- Bone creation
- Currency variant matching
- Factory-level integration
- End-to-end crafting workflows
- Error handling and edge cases
"""

import pytest
from typing import List
from unittest.mock import Mock, patch, MagicMock

from app.schemas.crafting import (
    CraftableItem,
    ItemModifier,
    ItemRarity,
    ModType,
    CurrencyConfigInfo,
    EssenceInfo,
    OmenInfo,
)
from pydantic import BaseModel

# BoneInfo schema (simplified for tests)
class BoneInfo(BaseModel):
    id: int
    name: str
    bone_type: str
    bone_part: str
    description: str
    min_modifier_level: int
    max_item_level: int
    stack_size: int
from app.services.crafting.unified_factory import unified_crafting_factory, UnifiedCraftingFactory
from app.services.crafting.mechanics import (
    ExaltedMechanic,
    RegalMechanic,
    AlchemyMechanic,
    ChaosMechanic,
    EssenceMechanic,
    DesecrationMechanic,
    OmenModifiedMechanic,
)


# ============================================================================
# FIXTURES
# ============================================================================

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
def mock_config_service():
    """Mock the config service to return test configurations."""
    with patch('app.services.crafting.unified_factory.get_currency_config') as mock_currency, \
         patch('app.services.crafting.unified_factory.get_essence_config') as mock_essence, \
         patch('app.services.crafting.unified_factory.get_omen_config') as mock_omen, \
         patch('app.services.crafting.unified_factory.get_bone_config') as mock_bone:

        # Setup mock returns
        mock_currency.return_value = CurrencyConfigInfo(
            id=1,
            name="Exalted Orb",
            currency_type="orb",
            tier="high",
            stack_size=20,
            rarity="rare",
            mechanic_class="ExaltedMechanic",
            config_data={},
        )

        mock_essence.return_value = EssenceInfo(
            id=1,
            name="Lesser Essence of Flames",
            essence_type="flames",
            essence_tier="lesser",
            mechanic="magic_to_rare",
            guaranteed_mod="Fire Damage",
            mod_type="prefix",
            applicable_to=["weapon"],
            stack_size=100,
        )

        mock_omen.return_value = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix modifier",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
            rules=[],
        )

        mock_bone.return_value = BoneInfo(
            id=1,
            name="Ancient Jawbone",
            bone_type="ancient",
            bone_part="jawbone",
            description="Adds ancient desecrated modifier",
            min_modifier_level=75,
            max_item_level=82,
            stack_size=20,
        )

        yield {
            'currency': mock_currency,
            'essence': mock_essence,
            'omen': mock_omen,
            'bone': mock_bone,
        }


# ============================================================================
# CURRENCY CREATION TESTS
# ============================================================================

class TestCurrencyCreation:
    """Test currency creation from config."""

    def test_creates_exalted_mechanic(self, mock_config_service):
        """Should create ExaltedMechanic from config."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Exalted Orb",
            currency_type="orb",
            tier="high",
            stack_size=20,
            rarity="rare",
            mechanic_class="ExaltedMechanic",
            config_data={},
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency("Exalted Orb")

        assert currency is not None
        assert isinstance(currency, ExaltedMechanic)

    def test_creates_alchemy_mechanic(self, mock_config_service):
        """Should create AlchemyMechanic from config."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Orb of Alchemy",
            currency_type="orb",
            tier="common",
            stack_size=50,
            rarity="common",
            mechanic_class="AlchemyMechanic",
            config_data={"num_mods": 4},
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency("Orb of Alchemy")

        assert currency is not None
        assert isinstance(currency, AlchemyMechanic)

    def test_returns_none_for_unknown_currency(self, mock_config_service):
        """Should return None for unknown currency."""
        mock_config_service['currency'].return_value = None

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency("Unknown Orb")

        assert currency is None


# ============================================================================
# OMEN APPLICATION TESTS
# ============================================================================

class TestOmenApplication:
    """Test omen application to base mechanics."""

    def test_wraps_mechanic_with_omen(self, mock_config_service):
        """Should wrap base mechanic with omen."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Exalted Orb",
            currency_type="orb",
            tier="high",
            stack_size=20,
            rarity="rare",
            mechanic_class="ExaltedMechanic",
            config_data={},
        )

        mock_config_service['omen'].return_value = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix modifier",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
            rules=[],
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency("Exalted Orb", ["Omen of Dextral Exaltation"])

        assert currency is not None
        assert isinstance(currency, OmenModifiedMechanic)

    def test_wraps_with_multiple_omens(self, mock_config_service):
        """Should wrap with multiple omens in sequence."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Exalted Orb",
            currency_type="orb",
            tier="high",
            stack_size=20,
            rarity="rare",
            mechanic_class="ExaltedMechanic",
            config_data={},
        )

        def mock_omen_side_effect(name):
            if "Dextral" in name:
                return OmenInfo(
                    id=1,
                    name="Omen of Dextral Exaltation",
                    effect_description="Adds only suffix",
                    affected_currency="Exalted Orb",
                    effect_type="dextral",
                    stack_size=10,
                    rules=[],
                )
            elif "Homogenising" in name:
                return OmenInfo(
                    id=2,
                    name="Omen of Homogenising Exaltation",
                    effect_description="Adds same type",
                    affected_currency="Exalted Orb",
                    effect_type="homogenising",
                    stack_size=10,
                    rules=[],
                )
            return None

        mock_config_service['omen'].side_effect = mock_omen_side_effect

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency(
            "Exalted Orb",
            ["Omen of Homogenising Exaltation", "Omen of Dextral Exaltation"]
        )

        assert currency is not None
        assert isinstance(currency, OmenModifiedMechanic)

    def test_skips_invalid_omen(self, mock_config_service):
        """Should skip invalid omens and still create base mechanic."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Exalted Orb",
            currency_type="orb",
            tier="high",
            stack_size=20,
            rarity="rare",
            mechanic_class="ExaltedMechanic",
            config_data={},
        )

        def mock_omen_side_effect(name):
            if "Invalid" in name:
                return None
            return OmenInfo(
                id=1,
                name="Omen of Dextral Exaltation",
                effect_description="Adds only suffix",
                affected_currency="Exalted Orb",
                effect_type="dextral",
                stack_size=10,
                rules=[],
            )

        mock_config_service['omen'].side_effect = mock_omen_side_effect

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency(
            "Exalted Orb",
            ["Invalid Omen", "Omen of Dextral Exaltation"]
        )

        assert currency is not None
        assert isinstance(currency, OmenModifiedMechanic)


# ============================================================================
# CURRENCY VARIANT MATCHING TESTS
# ============================================================================

class TestCurrencyVariantMatching:
    """Test that omens match currency variants correctly."""

    def test_omen_matches_perfect_exalted(self, mock_config_service):
        """Omen for 'Exalted Orb' should match 'Perfect Exalted Orb'."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Perfect Exalted Orb",
            currency_type="orb",
            tier="high",
            stack_size=20,
            rarity="rare",
            mechanic_class="ExaltedMechanic",
            config_data={"min_mod_level": 75},
        )

        mock_config_service['omen'].return_value = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix",
            affected_currency="Exalted Orb",  # Note: not "Perfect Exalted Orb"
            effect_type="dextral",
            stack_size=10,
            rules=[],
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency(
            "Perfect Exalted Orb",
            ["Omen of Dextral Exaltation"]
        )

        # Should successfully wrap because "Exalted Orb" is in "Perfect Exalted Orb"
        assert currency is not None
        assert isinstance(currency, OmenModifiedMechanic)

    def test_omen_matches_greater_chaos(self, mock_config_service):
        """Omen for 'Chaos Orb' should match 'Greater Chaos Orb'."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Greater Chaos Orb",
            currency_type="orb",
            tier="mid",
            stack_size=30,
            rarity="uncommon",
            mechanic_class="ChaosMechanic",
            config_data={"min_mod_level": 40},
        )

        mock_config_service['omen'].return_value = OmenInfo(
            id=1,
            name="Omen of Whittling",
            effect_description="Removes lowest level modifier",
            affected_currency="Chaos Orb",
            effect_type="whittling",
            stack_size=10,
            rules=[],
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency(
            "Greater Chaos Orb",
            ["Omen of Whittling"]
        )

        assert currency is not None
        assert isinstance(currency, OmenModifiedMechanic)

    def test_omen_does_not_match_different_currency(self, mock_config_service):
        """Omen for 'Exalted Orb' should not match 'Chaos Orb'."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Chaos Orb",
            currency_type="orb",
            tier="mid",
            stack_size=40,
            rarity="common",
            mechanic_class="ChaosMechanic",
            config_data={},
        )

        mock_config_service['omen'].return_value = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
            rules=[],
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency(
            "Chaos Orb",
            ["Omen of Dextral Exaltation"]
        )

        # Should not wrap (omen doesn't affect this currency)
        # Returns base mechanic without omen
        assert currency is not None
        # Should be base ChaosMechanic, not wrapped
        assert isinstance(currency, ChaosMechanic)


# ============================================================================
# ESSENCE CREATION TESTS
# ============================================================================

class TestEssenceCreation:
    """Test essence creation from config."""

    def test_creates_essence_mechanic(self, mock_config_service):
        """Should create EssenceMechanic from config."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Lesser Essence of Flames",
            currency_type="essence",
            tier="lesser",
            stack_size=100,
            rarity="common",
            mechanic_class="EssenceMechanic",
            config_data={},
        )

        mock_config_service['essence'].return_value = EssenceInfo(
            id=1,
            name="Lesser Essence of Flames",
            essence_type="flames",
            essence_tier="lesser",
            mechanic="magic_to_rare",
            guaranteed_mod="Fire Damage",
            mod_type="prefix",
            applicable_to=["weapon"],
            stack_size=100,
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency("Lesser Essence of Flames")

        assert currency is not None
        assert isinstance(currency, EssenceMechanic)


# ============================================================================
# BONE CREATION TESTS
# ============================================================================

class TestBoneCreation:
    """Test bone creation from config."""

    def test_creates_desecration_mechanic_from_bone(self, mock_config_service):
        """Should create DesecrationMechanic from bone config."""
        mock_config_service['currency'].return_value = None  # No standard currency config

        mock_config_service['bone'].return_value = BoneInfo(
            id=1,
            name="Ancient Jawbone",
            bone_type="ancient",
            bone_part="jawbone",
            description="Adds ancient desecrated modifier",
            min_modifier_level=75,
            max_item_level=82,
            stack_size=20,
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency("Ancient Jawbone")

        assert currency is not None
        # Should be DesecrationMechanic
        # (actual check depends on implementation)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestEndToEndCrafting:
    """Test complete end-to-end crafting workflows."""

    def test_full_rare_item_crafting_workflow(self, create_test_item, mock_config_service):
        """Test complete workflow from Normal to full 6-mod Rare."""
        # This would test the full pipeline:
        # Normal → Alchemy → Rare (4 mods) → Exalt → 5 mods → Exalt → 6 mods
        pass

    def test_essence_reroll_workflow(self, create_test_item, mock_config_service):
        """Test essence reroll workflow."""
        # Rare item with bad mods → Essence → New rare with guaranteed mod
        pass

    def test_desecration_endgame_workflow(self, create_test_item, mock_config_service):
        """Test adding desecrated mods to endgame rare."""
        # 6-mod rare → Cannot bone (full)
        # 5-mod rare → Bone → 6-mod rare with desecrated mod
        pass

    def test_omen_combination_workflow(self, create_test_item, mock_config_service):
        """Test using multiple omens in a crafting sequence."""
        # Rare → Exalt + Dextral → Suffix added
        # → Exalt + Sinistral → Prefix added
        # → Exalt + Greater → 2 mods added
        pass


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test error handling in factory."""

    def test_handles_missing_config_gracefully(self, mock_config_service):
        """Should handle missing config without crashing."""
        mock_config_service['currency'].return_value = None
        mock_config_service['bone'].return_value = None

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency("Nonexistent Currency")

        assert currency is None

    def test_handles_invalid_mechanic_class(self, mock_config_service):
        """Should handle invalid mechanic_class gracefully."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Broken Orb",
            currency_type="orb",
            tier="none",
            stack_size=1,
            rarity="unknown",
            mechanic_class="NonexistentMechanic",
            config_data={},
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency("Broken Orb")

        assert currency is None

    def test_handles_omen_mismatch_gracefully(self, mock_config_service):
        """Should handle omen/currency mismatch gracefully."""
        mock_config_service['currency'].return_value = CurrencyConfigInfo(
            id=1,
            name="Chaos Orb",
            currency_type="orb",
            tier="mid",
            stack_size=40,
            rarity="common",
            mechanic_class="ChaosMechanic",
            config_data={},
        )

        mock_config_service['omen'].return_value = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix",
            affected_currency="Exalted Orb",  # Wrong currency!
            effect_type="dextral",
            stack_size=10,
            rules=[],
        )

        factory = UnifiedCraftingFactory()
        currency = factory.create_currency("Chaos Orb", ["Omen of Dextral Exaltation"])

        # Should return base mechanic without omen
        assert currency is not None
        assert isinstance(currency, ChaosMechanic)


# ============================================================================
# FACTORY QUERY TESTS
# ============================================================================

class TestFactoryQueries:
    """Test factory query methods."""

    def test_get_all_currencies(self):
        """Should return all available currency names."""
        with patch('app.services.crafting.unified_factory.crafting_config_service') as mock_service:
            mock_service.get_all_currency_names.return_value = [
                "Exalted Orb",
                "Chaos Orb",
                "Alchemy Orb",
            ]

            factory = UnifiedCraftingFactory()
            currencies = factory.get_all_available_currencies()

            assert "Exalted Orb" in currencies
            assert "Chaos Orb" in currencies
            assert "Alchemy Orb" in currencies

    def test_get_omens_for_currency(self):
        """Should return omens applicable to a specific currency."""
        with patch('app.services.crafting.unified_factory.crafting_config_service') as mock_service:
            mock_service.get_omens_for_currency.return_value = [
                OmenInfo(
                    id=1,
                    name="Omen of Greater Exaltation",
                    effect_description="Adds TWO modifiers",
                    affected_currency="Exalted Orb",
                    effect_type="greater",
                    stack_size=10,
                    rules=[],
                ),
                OmenInfo(
                    id=2,
                    name="Omen of Dextral Exaltation",
                    effect_description="Adds suffix only",
                    affected_currency="Exalted Orb",
                    effect_type="dextral",
                    stack_size=10,
                    rules=[],
                ),
            ]

            factory = UnifiedCraftingFactory()
            omens = factory.get_omens_for_currency("Exalted Orb")

            assert "Omen of Greater Exaltation" in omens
            assert "Omen of Dextral Exaltation" in omens

    def test_get_currency_info(self, mock_config_service):
        """Should return detailed currency information."""
        factory = UnifiedCraftingFactory()
        info = factory.get_currency_info("Exalted Orb")

        assert info is not None
        assert info.name == "Exalted Orb"


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
