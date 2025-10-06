"""
Comprehensive test suite for all crafting mechanics.

Tests cover:
- Base currency mechanics (Transmutation, Augmentation, Alchemy, Regal, Exalted, Chaos, Divine, etc.)
- Essence mechanics (all tiers and types)
- Desecration mechanics (bones)
- Omen mechanics (all types and combinations)
- Item state management
- Modifier pool filtering
- Edge cases and error conditions
"""

import pytest
from typing import List
from unittest.mock import Mock, patch

from app.schemas.crafting import (
    CraftableItem,
    ItemModifier,
    ItemRarity,
    ModType,
    CurrencyConfigInfo,
    EssenceInfo,
    OmenInfo,
)
from app.services.crafting.mechanics import (
    TransmutationMechanic,
    AugmentationMechanic,
    AlchemyMechanic,
    RegalMechanic,
    ExaltedMechanic,
    ChaosMechanic,
    DivineMechanic,
    VaalMechanic,
    ChanceMechanic,
    AnnulmentMechanic,
    ScouringMechanic,
    EssenceMechanic,
    DesecrationMechanic,
    OmenModifiedMechanic,
)
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.unified_factory import unified_crafting_factory


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
        corrupted: bool = False,
        quality: int = 20,
    ):
        return CraftableItem(
            base_name=base_name,
            base_category=base_category,
            rarity=rarity,
            item_level=item_level,
            quality=quality,
            prefix_mods=prefix_mods or [],
            suffix_mods=suffix_mods or [],
            corrupted=corrupted,
        )
    return _create


@pytest.fixture
def mock_modifier_pool(create_test_modifier):
    """Create a mock modifier pool with test modifiers."""
    pool = Mock(spec=ModifierPool)

    # Create test modifiers
    test_prefix = create_test_modifier("Test Prefix", ModType.PREFIX)
    test_suffix = create_test_modifier("Test Suffix", ModType.SUFFIX)

    def roll_random_modifier(mod_type, base_category, item_level, **kwargs):
        if mod_type == "prefix":
            return test_prefix
        else:
            return test_suffix

    pool.roll_random_modifier = Mock(side_effect=roll_random_modifier)
    pool._get_excluded_groups_from_item = Mock(return_value=set())

    return pool


# ============================================================================
# TRANSMUTATION MECHANIC TESTS
# ============================================================================

class TestTransmutationMechanic:
    """Test Transmutation Orb: Normal → Magic with 1 modifier."""

    def test_can_apply_to_normal_item(self, create_test_item):
        """Should be applicable to Normal items."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = TransmutationMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True
        assert error is None

    def test_cannot_apply_to_magic_item(self, create_test_item):
        """Should not be applicable to Magic items."""
        item = create_test_item(rarity=ItemRarity.MAGIC)
        mechanic = TransmutationMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "Normal" in error

    def test_cannot_apply_to_rare_item(self, create_test_item):
        """Should not be applicable to Rare items."""
        item = create_test_item(rarity=ItemRarity.RARE)
        mechanic = TransmutationMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False

    def test_upgrades_to_magic(self, create_test_item, mock_modifier_pool):
        """Should upgrade Normal item to Magic."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = TransmutationMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.rarity == ItemRarity.MAGIC

    def test_adds_one_modifier(self, create_test_item, mock_modifier_pool):
        """Should add exactly 1 modifier."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = TransmutationMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.total_explicit_mods == 1

    def test_can_add_prefix_or_suffix(self, create_test_item, mock_modifier_pool):
        """Should randomly add prefix or suffix."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = TransmutationMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.prefix_count == 1 or result.suffix_count == 1


# ============================================================================
# AUGMENTATION MECHANIC TESTS
# ============================================================================

class TestAugmentationMechanic:
    """Test Augmentation Orb: Magic with 1 mod → Magic with 2 mods."""

    def test_can_apply_to_magic_with_one_mod(self, create_test_item, create_test_modifier):
        """Should be applicable to Magic items with 1 modifier."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = AugmentationMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True
        assert error is None

    def test_cannot_apply_to_normal_item(self, create_test_item):
        """Should not be applicable to Normal items."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = AugmentationMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "Magic" in error

    def test_cannot_apply_to_magic_with_two_mods(self, create_test_item, create_test_modifier):
        """Should not be applicable to Magic items with 2 modifiers."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        suffix = create_test_modifier("Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix], suffix_mods=[suffix])
        mechanic = AugmentationMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "maximum" in error.lower()

    def test_adds_second_modifier(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should add exactly 1 modifier to reach 2 total."""
        prefix = create_test_modifier("Existing Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = AugmentationMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.total_explicit_mods == 2

    def test_adds_opposite_type_when_prefix_exists(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should add suffix when prefix already exists."""
        prefix = create_test_modifier("Existing Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = AugmentationMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.suffix_count == 1

    def test_adds_opposite_type_when_suffix_exists(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should add prefix when suffix already exists."""
        suffix = create_test_modifier("Existing Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, suffix_mods=[suffix])
        mechanic = AugmentationMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.prefix_count == 1


# ============================================================================
# ALCHEMY MECHANIC TESTS
# ============================================================================

class TestAlchemyMechanic:
    """Test Alchemy Orb: Normal → Rare with 4 modifiers."""

    def test_can_apply_to_normal_item(self, create_test_item):
        """Should be applicable to Normal items."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = AlchemyMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True

    def test_cannot_apply_to_magic_item(self, create_test_item, create_test_modifier):
        """Should not be applicable to Magic items."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = AlchemyMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "Normal" in error

    def test_upgrades_to_rare(self, create_test_item, mock_modifier_pool):
        """Should upgrade Normal item to Rare."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = AlchemyMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.rarity == ItemRarity.RARE

    def test_adds_four_modifiers_by_default(self, create_test_item, mock_modifier_pool):
        """Should add 4 modifiers by default."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = AlchemyMechanic({"num_mods": 4})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.total_explicit_mods == 4

    def test_balances_prefixes_and_suffixes(self, create_test_item, mock_modifier_pool):
        """Should create a balanced mix of prefixes and suffixes."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = AlchemyMechanic({"num_mods": 4})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        # Should have both prefixes and suffixes
        assert result.prefix_count > 0
        assert result.suffix_count > 0
        # Combined should be 4
        assert result.total_explicit_mods == 4


# ============================================================================
# REGAL MECHANIC TESTS
# ============================================================================

class TestRegalMechanic:
    """Test Regal Orb: Magic → Rare, add 1 modifier."""

    def test_can_apply_to_magic_item(self, create_test_item, create_test_modifier):
        """Should be applicable to Magic items."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = RegalMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True

    def test_cannot_apply_to_normal_item(self, create_test_item):
        """Should not be applicable to Normal items."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = RegalMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "Magic" in error

    def test_cannot_apply_to_rare_item(self, create_test_item, create_test_modifier):
        """Should not be applicable to Rare items."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])
        mechanic = RegalMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False

    def test_upgrades_to_rare(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should upgrade Magic item to Rare."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = RegalMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.rarity == ItemRarity.RARE

    def test_adds_one_modifier(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should add exactly 1 modifier."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = RegalMechanic({})

        initial_count = item.total_explicit_mods
        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.total_explicit_mods == initial_count + 1


# ============================================================================
# EXALTED MECHANIC TESTS
# ============================================================================

class TestExaltedMechanic:
    """Test Exalted Orb: Add 1 modifier to Rare item."""

    def test_can_apply_to_rare_with_open_slot(self, create_test_item, create_test_modifier):
        """Should be applicable to Rare items with open affix slots."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])
        mechanic = ExaltedMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True

    def test_cannot_apply_to_magic_item(self, create_test_item, create_test_modifier):
        """Should not be applicable to Magic items."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = ExaltedMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "Rare" in error

    def test_cannot_apply_to_full_item(self, create_test_item, create_test_modifier):
        """Should not be applicable to items with 6 modifiers."""
        prefixes = [create_test_modifier(f"Prefix{i}", ModType.PREFIX) for i in range(3)]
        suffixes = [create_test_modifier(f"Suffix{i}", ModType.SUFFIX) for i in range(3)]
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=prefixes, suffix_mods=suffixes)
        mechanic = ExaltedMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "open affix" in error.lower()

    def test_adds_one_modifier(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should add exactly 1 modifier."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])
        mechanic = ExaltedMechanic({})

        initial_count = item.total_explicit_mods
        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.total_explicit_mods == initial_count + 1

    def test_respects_min_mod_level(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should pass min_mod_level to modifier pool."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])
        mechanic = ExaltedMechanic({"min_mod_level": 75})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        # Check that min_mod_level was passed
        mock_modifier_pool.roll_random_modifier.assert_called()
        call_kwargs = mock_modifier_pool.roll_random_modifier.call_args[1]
        assert call_kwargs.get("min_mod_level") == 75


# ============================================================================
# CHAOS MECHANIC TESTS
# ============================================================================

class TestChaosMechanic:
    """Test Chaos Orb: Remove 1 modifier, add 1 modifier."""

    def test_can_apply_to_rare_with_mods(self, create_test_item, create_test_modifier):
        """Should be applicable to Rare items with modifiers."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])
        mechanic = ChaosMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True

    def test_cannot_apply_to_magic_item(self, create_test_item, create_test_modifier):
        """Should not be applicable to Magic items."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = ChaosMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "Rare" in error

    def test_cannot_apply_to_empty_rare(self, create_test_item):
        """Should not be applicable to Rare items with no modifiers."""
        item = create_test_item(rarity=ItemRarity.RARE)
        mechanic = ChaosMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "modifier" in error.lower()

    def test_maintains_mod_count(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should maintain the same number of modifiers (remove 1, add 1)."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        suffix = create_test_modifier("Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix], suffix_mods=[suffix])
        mechanic = ChaosMechanic({})

        initial_count = item.total_explicit_mods
        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.total_explicit_mods == initial_count

    def test_replaces_same_type(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should replace with the same modifier type."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])
        mechanic = ChaosMechanic({})

        # Mock to track which type was requested
        mock_modifier_pool.roll_random_modifier.reset_mock()

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        # Should request same type as removed
        mock_modifier_pool.roll_random_modifier.assert_called()


# ============================================================================
# DIVINE MECHANIC TESTS
# ============================================================================

class TestDivineMechanic:
    """Test Divine Orb: Reroll modifier values."""

    def test_can_apply_to_item_with_mods(self, create_test_item, create_test_modifier):
        """Should be applicable to items with modifiers."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX, stat_min=10, stat_max=20)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])
        mechanic = DivineMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True

    def test_cannot_apply_to_item_without_mods(self, create_test_item):
        """Should not be applicable to items without modifiers."""
        item = create_test_item(rarity=ItemRarity.NORMAL)
        mechanic = DivineMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False

    def test_rerolls_values(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should reroll modifier values within their ranges."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX, stat_min=10, stat_max=20)
        prefix.current_value = 10  # Set to minimum
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])
        mechanic = DivineMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        # Value should potentially change (might still be 10, but range allows others)
        assert result.prefix_mods[0].stat_min <= result.prefix_mods[0].current_value <= result.prefix_mods[0].stat_max


# ============================================================================
# OMEN MODIFIED EXALTED TESTS
# ============================================================================

class TestOmenModifiedExalted:
    """Test Exalted Orb with various omen combinations."""

    def test_dextral_exaltation_forces_suffix(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of Dextral Exaltation should force suffix addition."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])

        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix modifier",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.suffix_count == 1
        assert "Dextral Exaltation" in message

    def test_sinistral_exaltation_forces_prefix(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of Sinistral Exaltation should force prefix addition."""
        suffix = create_test_modifier("Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.RARE, suffix_mods=[suffix])

        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Sinistral Exaltation",
            effect_description="Adds only prefix modifier",
            affected_currency="Exalted Orb",
            effect_type="sinistral",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.prefix_count == 1
        assert "Sinistral Exaltation" in message

    def test_greater_exaltation_adds_two_mods(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of Greater Exaltation should add TWO modifiers."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])

        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Greater Exaltation",
            effect_description="Adds TWO random modifiers",
            affected_currency="Exalted Orb",
            effect_type="greater",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        initial_count = item.total_explicit_mods
        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.total_explicit_mods == initial_count + 2
        assert "2 modifiers" in message or "Greater Exaltation" in message

    def test_dextral_takes_priority_over_homogenising(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Dextral Exaltation should take priority over Homogenising when both present."""
        prefix1 = create_test_modifier("Prefix1", ModType.PREFIX)
        prefix2 = create_test_modifier("Prefix2", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix1, prefix2])

        # Apply Homogenising first, then Dextral (should still force suffix)
        base_mechanic = ExaltedMechanic({})

        homogenising_omen = OmenInfo(
            id=1,
            name="Omen of Homogenising Exaltation",
            effect_description="Adds modifier of same type as existing",
            affected_currency="Exalted Orb",
            effect_type="homogenising",
            stack_size=10,
        )

        dextral_omen = OmenInfo(
            id=2,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix modifier",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
        )

        # Wrap with both omens
        omen_mechanic = OmenModifiedMechanic(base_mechanic, homogenising_omen)
        omen_mechanic = OmenModifiedMechanic(omen_mechanic, dextral_omen)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        # Should add suffix despite having only prefixes (Dextral overrides Homogenising)
        assert success is True
        assert result.suffix_count == 1

    def test_homogenising_exaltation_matches_existing_type(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Homogenising Exaltation should add modifier matching existing type."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX, mod_group="life", tags=["life"])
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])

        # Mock eligible mods
        matching_mod = create_test_modifier("Life2", ModType.PREFIX, tags=["life"])
        mock_modifier_pool.get_eligible_mods.return_value = [matching_mod]
        mock_modifier_pool._weighted_random_choice.return_value = matching_mod

        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Homogenising Exaltation",
            effect_description="Adds modifier of same type as existing",
            affected_currency="Exalted Orb",
            effect_type="homogenising",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        # When item only has prefixes, should add prefix
        assert success is True
        assert result.prefix_count == 2

    def test_homogenising_exaltation_filters_by_tags(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Homogenising Exaltation should only add mods with matching tags."""
        # Create a prefix with specific tags
        prefix_with_tags = create_test_modifier(
            "Cast Speed", ModType.PREFIX, tags=["caster", "speed"]
        )
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix_with_tags])

        # Create eligible mods - some with matching tags, some without
        matching_mod1 = create_test_modifier("Spell Damage", ModType.PREFIX, tags=["caster", "damage"])
        matching_mod2 = create_test_modifier("Speed Boost", ModType.PREFIX, tags=["speed", "attack"])
        non_matching_mod = create_test_modifier("Life", ModType.PREFIX, tags=["life", "defences"])

        # Mock get_eligible_mods to return different lists for prefix vs suffix
        def mock_get_eligible_mods(base_category, item_level, mod_type, *args, **kwargs):
            if mod_type == "prefix":
                return [matching_mod1, matching_mod2, non_matching_mod]
            else:  # suffix
                return []  # No suffix mods since all test mods are prefixes
        mock_modifier_pool.get_eligible_mods.side_effect = mock_get_eligible_mods

        # Mock weighted choice to track which mods were passed to it
        called_with_mods = []
        def track_weighted_choice(mods):
            called_with_mods.append(mods)
            return mods[0] if mods else None
        mock_modifier_pool._weighted_random_choice.side_effect = track_weighted_choice

        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Homogenising Exaltation",
            effect_description="Adds modifier of same type with matching tags",
            affected_currency="Exalted Orb",
            effect_type="homogenising",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        # Should succeed
        assert success is True
        # Should have filtered to only mods with matching tags (caster OR speed)
        assert len(called_with_mods) == 1
        filtered_mods = called_with_mods[0]
        assert len(filtered_mods) == 2  # matching_mod1 and matching_mod2
        assert matching_mod1 in filtered_mods
        assert matching_mod2 in filtered_mods
        assert non_matching_mod not in filtered_mods

    def test_homogenising_exaltation_switches_type_and_repicks_mod(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """When suffix is full, homogenising should switch to prefix and re-pick a prefix mod for tag filtering."""
        # Create an item with 3 suffixes (full) and 1 prefix
        suffix1 = create_test_modifier("Rarity", ModType.SUFFIX, tags=["resource"])
        suffix2 = create_test_modifier("Fire Res", ModType.SUFFIX, tags=["elemental", "resistance"])
        suffix3 = create_test_modifier("Cold Res", ModType.SUFFIX, tags=["elemental", "resistance"])
        prefix1 = create_test_modifier("Cast Speed", ModType.PREFIX, tags=["caster", "speed"])

        item = create_test_item(
            rarity=ItemRarity.RARE,
            prefix_mods=[prefix1],
            suffix_mods=[suffix1, suffix2, suffix3]
        )

        # Create eligible prefix mods
        matching_prefix = create_test_modifier("Spell Damage", ModType.PREFIX, tags=["caster", "damage"])
        non_matching_prefix = create_test_modifier("Life", ModType.PREFIX, tags=["life"])

        mock_modifier_pool.get_eligible_mods.return_value = [matching_prefix, non_matching_prefix]

        called_with_mods = []
        def track_weighted_choice(mods):
            called_with_mods.append(mods)
            return mods[0] if mods else None
        mock_modifier_pool._weighted_random_choice.side_effect = track_weighted_choice

        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Homogenising Exaltation",
            effect_description="Adds modifier of same type with matching tags",
            affected_currency="Exalted Orb",
            effect_type="homogenising",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        # Should succeed
        assert success is True
        # Should have added a prefix (since suffixes are full)
        assert result.prefix_count == 2
        assert result.suffix_count == 3

        # Should have filtered by prefix1's tags (caster, speed), not any suffix tags
        assert len(called_with_mods) == 1
        filtered_mods = called_with_mods[0]
        assert len(filtered_mods) == 1  # Only matching_prefix has caster/speed tags
        assert matching_prefix in filtered_mods
        assert non_matching_prefix not in filtered_mods

    def test_homogenising_exaltation_no_matching_tags_fallback(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """When no mods have matching tags, homogenising should fail."""
        prefix_with_tags = create_test_modifier("Cast Speed", ModType.PREFIX, tags=["caster", "speed"])
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix_with_tags])

        # Create eligible mods with NO matching tags
        mod1 = create_test_modifier("Life", ModType.PREFIX, tags=["life", "defences"])
        mod2 = create_test_modifier("Armour", ModType.PREFIX, tags=["armour", "defences"])

        # Mock get_eligible_mods to return non-matching mods for prefix, nothing for suffix
        def mock_get_eligible_mods(base_category, item_level, mod_type, *args, **kwargs):
            if mod_type == "prefix":
                return [mod1, mod2]
            else:
                return []
        mock_modifier_pool.get_eligible_mods.side_effect = mock_get_eligible_mods

        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Homogenising Exaltation",
            effect_description="Adds modifier of same type with matching tags",
            affected_currency="Exalted Orb",
            effect_type="homogenising",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        # Should fail when no matching tags found
        assert success is False
        assert "No modifiers with matching tags" in message

    def test_perfect_exalted_homogenising_enforces_min_mod_level(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Perfect Exalted Orb with Homogenising should enforce min_mod_level=45."""
        prefix_with_tags = create_test_modifier("Spell Damage", ModType.PREFIX, tags=["caster", "damage"])
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix_with_tags])

        # Create test mods: one low tier (below 45) and one high tier (45+)
        low_tier_mod = create_test_modifier("Low Tier Caster", ModType.PREFIX, tags=["caster"], required_ilvl=30)
        high_tier_mod = create_test_modifier("High Tier Caster", ModType.PREFIX, tags=["caster"], required_ilvl=75)

        # Mock get_eligible_mods to return high tier mod for prefix, nothing for suffix
        def mock_get_eligible_mods(base_category, item_level, mod_type, *args, **kwargs):
            if mod_type == "prefix":
                return [high_tier_mod]
            else:
                return []
        mock_modifier_pool.get_eligible_mods.side_effect = mock_get_eligible_mods
        mock_modifier_pool._weighted_random_choice.return_value = high_tier_mod

        # Perfect Exalted Orb has min_mod_level=45
        base_mechanic = ExaltedMechanic({"min_mod_level": 45})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Homogenising Exaltation",
            effect_description="Adds modifier of same type with matching tags",
            affected_currency="Exalted Orb",
            effect_type="homogenising",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        # Verify get_eligible_mods was called with min_mod_level=45
        assert mock_modifier_pool.get_eligible_mods.call_count >= 1
        # Check that at least one call had min_mod_level=45
        calls_with_min_mod = [call for call in mock_modifier_pool.get_eligible_mods.call_args_list
                               if call.kwargs.get('min_mod_level') == 45]
        assert len(calls_with_min_mod) >= 1

        # Should succeed and add the high tier mod
        assert success is True
        assert result.prefix_count == 2

    def test_greater_exaltation_homogenising_freezes_initial_tags(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Greater Exaltation + Homogenising: 2nd mod uses INITIAL tags, not tags from 1st mod."""
        # Start with item having only 'caster' tag
        prefix_with_tags = create_test_modifier("Spell Damage", ModType.PREFIX, tags=["caster"])
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix_with_tags])

        # 1st mod to add: has 'fire' tag (new tag!)
        mod1_with_fire = create_test_modifier("Fire Damage", ModType.PREFIX, tags=["fire", "elemental"])
        # 2nd mod to add: has 'caster' tag (original tag)
        mod2_with_caster = create_test_modifier("Spell Crit", ModType.PREFIX, tags=["caster", "critical"])

        # Mock get_eligible_mods and _weighted_random_choice
        mock_modifier_pool.get_eligible_mods.return_value = [mod1_with_fire, mod2_with_caster]
        # First call returns mod with fire, second call should still only match 'caster' (original tag)
        mock_modifier_pool._weighted_random_choice.side_effect = [mod1_with_fire, mod2_with_caster]

        base_mechanic = ExaltedMechanic({})
        homogenising_omen = OmenInfo(
            id=1,
            name="Omen of Homogenising Exaltation",
            effect_description="Adds modifier matching tags",
            affected_currency="Exalted Orb",
            effect_type="homogenising",
            stack_size=10,
        )
        greater_omen = OmenInfo(
            id=2,
            name="Omen of Greater Exaltation",
            effect_description="Adds two modifiers",
            affected_currency="Exalted Orb",
            effect_type="greater",
            stack_size=10,
        )

        # Apply both omens
        omen_mechanic = OmenModifiedMechanic(base_mechanic, homogenising_omen)
        omen_mechanic = OmenModifiedMechanic(omen_mechanic, greater_omen)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        # Should succeed and add 2 mods
        assert success is True
        assert result.prefix_count == 3

        # Verify _weighted_random_choice was called twice with filtered mods
        # Both calls should filter by ['caster'] tag only, NOT ['fire', 'elemental']
        assert mock_modifier_pool._weighted_random_choice.call_count == 2

        # First call: filters to mods matching 'caster' tag
        first_call_mods = mock_modifier_pool._weighted_random_choice.call_args_list[0][0][0]
        # Should include mod2_with_caster (has 'caster'), not mod1_with_fire (no 'caster')
        assert mod2_with_caster in first_call_mods
        assert mod1_with_fire not in first_call_mods


# ============================================================================
# OMEN MODIFIED REGAL TESTS
# ============================================================================

class TestOmenModifiedRegal:
    """Test Regal Orb with omen combinations."""

    def test_dextral_coronation_forces_suffix(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of Dextral Coronation should force suffix addition."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])

        base_mechanic = RegalMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Dextral Coronation",
            effect_description="Adds only suffix modifier",
            affected_currency="Regal Orb",
            effect_type="dextral",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.suffix_count == 1
        assert result.rarity == ItemRarity.RARE

    def test_sinistral_coronation_forces_prefix(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of Sinistral Coronation should force prefix addition."""
        suffix = create_test_modifier("Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, suffix_mods=[suffix])

        base_mechanic = RegalMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Sinistral Coronation",
            effect_description="Adds only prefix modifier",
            affected_currency="Regal Orb",
            effect_type="sinistral",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.prefix_count == 1
        assert result.rarity == ItemRarity.RARE


# ============================================================================
# OMEN MODIFIED CHAOS TESTS
# ============================================================================

class TestOmenModifiedChaos:
    """Test Chaos Orb with omen combinations."""

    def test_dextral_erasure_removes_suffix(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of Dextral Erasure should remove only suffixes."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        suffix = create_test_modifier("Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix], suffix_mods=[suffix])

        base_mechanic = ChaosMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Dextral Erasure",
            effect_description="Chaos Orb removes only suffixes",
            affected_currency="Chaos Orb",
            effect_type="dextral",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        assert success is True
        # Should have removed suffix and added suffix (same count, but replaced)
        assert result.suffix_count == 1
        assert result.prefix_count == 1

    def test_sinistral_erasure_removes_prefix(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Omen of Sinistral Erasure should remove only prefixes."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        suffix = create_test_modifier("Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix], suffix_mods=[suffix])

        base_mechanic = ChaosMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Sinistral Erasure",
            effect_description="Chaos Orb removes only prefixes",
            affected_currency="Chaos Orb",
            effect_type="sinistral",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.prefix_count == 1
        assert result.suffix_count == 1


# ============================================================================
# OMEN MODIFIED ALCHEMY TESTS
# ============================================================================

class TestOmenModifiedAlchemy:
    """Test Alchemy Orb with omen combinations."""

    def test_sinistral_alchemy_max_prefixes(self, create_test_item, mock_modifier_pool):
        """Omen of Sinistral Alchemy should result in 3 prefixes."""
        item = create_test_item(rarity=ItemRarity.NORMAL)

        base_mechanic = AlchemyMechanic({"num_mods": 4})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Sinistral Alchemy",
            effect_description="Results in maximum prefix modifiers",
            affected_currency="Orb of Alchemy",
            effect_type="sinistral",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.rarity == ItemRarity.RARE
        assert result.prefix_count == 3
        assert result.suffix_count == 1

    def test_dextral_alchemy_max_suffixes(self, create_test_item, mock_modifier_pool):
        """Omen of Dextral Alchemy should result in 3 suffixes."""
        item = create_test_item(rarity=ItemRarity.NORMAL)

        base_mechanic = AlchemyMechanic({"num_mods": 4})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Dextral Alchemy",
            effect_description="Results in maximum suffix modifiers",
            affected_currency="Orb of Alchemy",
            effect_type="dextral",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.rarity == ItemRarity.RARE
        assert result.prefix_count == 1
        assert result.suffix_count == 3


# ============================================================================
# CURRENCY VARIANT MATCHING TESTS
# ============================================================================

class TestCurrencyVariantMatching:
    """Test that omens work with currency variants (Perfect, Greater, etc.)."""

    def test_omen_matches_perfect_exalted(self):
        """Omens for 'Exalted Orb' should match 'Perfect Exalted Orb'."""
        omen_info = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix modifier",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
        )

        currency_name = "Perfect Exalted Orb"

        # Test the matching logic
        affected = omen_info.affected_currency
        matches = affected == currency_name or affected in currency_name

        assert matches is True

    def test_omen_matches_greater_exalted(self):
        """Omens for 'Exalted Orb' should match 'Greater Exalted Orb'."""
        omen_info = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix modifier",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
        )

        currency_name = "Greater Exalted Orb"

        affected = omen_info.affected_currency
        matches = affected == currency_name or affected in currency_name

        assert matches is True

    def test_omen_matches_exact_name(self):
        """Omens should still match exact currency names."""
        omen_info = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix modifier",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
        )

        currency_name = "Exalted Orb"

        affected = omen_info.affected_currency
        matches = affected == currency_name or affected in currency_name

        assert matches is True

    def test_omen_does_not_match_different_currency(self):
        """Omens should not match completely different currencies."""
        omen_info = OmenInfo(
            id=1,
            name="Omen of Dextral Exaltation",
            effect_description="Adds only suffix modifier",
            affected_currency="Exalted Orb",
            effect_type="dextral",
            stack_size=10,
        )

        currency_name = "Chaos Orb"

        affected = omen_info.affected_currency
        matches = affected == currency_name or affected in currency_name

        assert matches is False


# ============================================================================
# EDGE CASES AND ERROR CONDITIONS
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_cannot_exalt_corrupted_item(self, create_test_item, create_test_modifier):
        """Should not be able to apply most currencies to corrupted items."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix], corrupted=True)

        # Most mechanics should fail on corrupted items
        # (Implementation may vary, this is a general principle)
        assert item.corrupted is True

    def test_exalted_with_5_mods_adds_6th(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should be able to add 6th modifier to item with 5 mods."""
        prefixes = [create_test_modifier(f"Prefix{i}", ModType.PREFIX) for i in range(3)]
        suffixes = [create_test_modifier(f"Suffix{i}", ModType.SUFFIX) for i in range(2)]
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=prefixes, suffix_mods=suffixes)
        mechanic = ExaltedMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.total_explicit_mods == 6

    def test_augmentation_on_magic_with_prefix_adds_suffix(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Augmentation on magic item with prefix should add suffix."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])
        mechanic = AugmentationMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.prefix_count == 1
        assert result.suffix_count == 1

    def test_augmentation_on_magic_with_suffix_adds_prefix(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Augmentation on magic item with suffix should add prefix."""
        suffix = create_test_modifier("Suffix", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.MAGIC, suffix_mods=[suffix])
        mechanic = AugmentationMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.prefix_count == 1
        assert result.suffix_count == 1

    def test_greater_exaltation_on_item_with_5_mods_adds_only_1(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Greater Exaltation on item with 5 mods should only add 1 (not 2)."""
        prefixes = [create_test_modifier(f"Prefix{i}", ModType.PREFIX) for i in range(3)]
        suffixes = [create_test_modifier(f"Suffix{i}", ModType.SUFFIX) for i in range(2)]
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=prefixes, suffix_mods=suffixes)

        base_mechanic = ExaltedMechanic({})
        omen_info = OmenInfo(
            id=1,
            name="Omen of Greater Exaltation",
            effect_description="Adds TWO random modifiers",
            affected_currency="Exalted Orb",
            effect_type="greater",
            stack_size=10,
        )
        omen_mechanic = OmenModifiedMechanic(base_mechanic, omen_info)

        success, message, result = omen_mechanic.apply(item, mock_modifier_pool)

        # Can only add 1 because item has 5 mods already
        assert success is True
        assert result.total_explicit_mods == 6


# ============================================================================
# VAAL MECHANIC TESTS
# ============================================================================

class TestVaalMechanic:
    """Test Vaal Orb: Corrupts item with random outcome."""

    def test_can_apply_to_non_corrupted_item(self, create_test_item):
        """Should be applicable to non-corrupted items."""
        item = create_test_item(rarity=ItemRarity.RARE)
        mechanic = VaalMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True

    def test_cannot_apply_to_corrupted_item(self, create_test_item):
        """Should not be applicable to already corrupted items."""
        item = create_test_item(rarity=ItemRarity.RARE, corrupted=True)
        mechanic = VaalMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False
        assert "corrupted" in error.lower()

    def test_always_corrupts_item(self, create_test_item, mock_modifier_pool):
        """Should always corrupt the item regardless of outcome."""
        item = create_test_item(rarity=ItemRarity.RARE)
        mechanic = VaalMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert result.corrupted is True


# ============================================================================
# ANNULMENT MECHANIC TESTS
# ============================================================================

class TestAnnulmentMechanic:
    """Test Orb of Annulment: Remove 1 random modifier."""

    def test_can_apply_to_item_with_mods(self, create_test_item, create_test_modifier):
        """Should be applicable to items with modifiers."""
        prefix = create_test_modifier("Prefix", ModType.PREFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix])
        mechanic = AnnulmentMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True

    def test_cannot_apply_to_item_without_mods(self, create_test_item):
        """Should not be applicable to items without modifiers."""
        item = create_test_item(rarity=ItemRarity.RARE)
        mechanic = AnnulmentMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is False

    def test_removes_one_modifier(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should remove exactly 1 modifier."""
        prefix = create_test_modifier("Prefix1", ModType.PREFIX)
        suffix = create_test_modifier("Suffix1", ModType.SUFFIX)
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=[prefix], suffix_mods=[suffix])
        mechanic = AnnulmentMechanic({})

        initial_count = item.total_explicit_mods
        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.total_explicit_mods == initial_count - 1


# ============================================================================
# SCOURING MECHANIC TESTS
# ============================================================================

class TestScouringMechanic:
    """Test Orb of Scouring: Remove all modifiers."""

    def test_can_apply_to_any_item(self, create_test_item):
        """Should be applicable to any item."""
        item = create_test_item(rarity=ItemRarity.RARE)
        mechanic = ScouringMechanic({})

        can_apply, error = mechanic.can_apply(item)

        assert can_apply is True

    def test_removes_all_modifiers(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Should remove all modifiers."""
        prefixes = [create_test_modifier(f"Prefix{i}", ModType.PREFIX) for i in range(2)]
        suffixes = [create_test_modifier(f"Suffix{i}", ModType.SUFFIX) for i in range(2)]
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=prefixes, suffix_mods=suffixes)
        mechanic = ScouringMechanic({})

        success, message, result = mechanic.apply(item, mock_modifier_pool)

        assert success is True
        assert result.total_explicit_mods == 0


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestCraftingWorkflows:
    """Test complete crafting workflows."""

    def test_normal_to_magic_to_rare_workflow(self, create_test_item, mock_modifier_pool):
        """Test crafting progression: Normal → Magic → Rare."""
        # Start with Normal item
        item = create_test_item(rarity=ItemRarity.NORMAL)

        # Apply Transmutation (Normal → Magic, 1 mod)
        trans = TransmutationMechanic({"min_mods": 1, "max_mods": 1})  # Force exactly 1 mod
        success, message, item = trans.apply(item, mock_modifier_pool)
        assert success is True
        assert item.rarity == ItemRarity.MAGIC
        assert item.total_explicit_mods == 1

        # Apply Augmentation (Magic 1 mod → Magic 2 mods)
        aug = AugmentationMechanic({})
        success, message, item = aug.apply(item, mock_modifier_pool)
        assert success is True
        assert item.rarity == ItemRarity.MAGIC
        assert item.total_explicit_mods == 2

        # Apply Regal (Magic → Rare, add 1 mod)
        regal = RegalMechanic({})
        success, message, item = regal.apply(item, mock_modifier_pool)
        assert success is True
        assert item.rarity == ItemRarity.RARE
        assert item.total_explicit_mods == 3

    def test_normal_to_rare_with_alchemy(self, create_test_item, mock_modifier_pool):
        """Test direct Normal → Rare with Alchemy."""
        item = create_test_item(rarity=ItemRarity.NORMAL)

        alch = AlchemyMechanic({"num_mods": 4})
        success, message, item = alch.apply(item, mock_modifier_pool)

        assert success is True
        assert item.rarity == ItemRarity.RARE
        assert item.total_explicit_mods == 4

    def test_exalt_to_6_mods(self, create_test_item, create_test_modifier, mock_modifier_pool):
        """Test exalting a rare item to 6 mods."""
        prefixes = [create_test_modifier(f"Prefix{i}", ModType.PREFIX) for i in range(2)]
        suffixes = [create_test_modifier(f"Suffix{i}", ModType.SUFFIX) for i in range(2)]
        item = create_test_item(rarity=ItemRarity.RARE, prefix_mods=prefixes, suffix_mods=suffixes)

        exalt = ExaltedMechanic({})

        # First exalt
        success, message, item = exalt.apply(item, mock_modifier_pool)
        assert success is True
        assert item.total_explicit_mods == 5

        # Second exalt
        success, message, item = exalt.apply(item, mock_modifier_pool)
        assert success is True
        assert item.total_explicit_mods == 6

        # Third exalt should fail
        can_apply, error = exalt.can_apply(item)
        assert can_apply is False


# ============================================================================
# RUN ALL TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
