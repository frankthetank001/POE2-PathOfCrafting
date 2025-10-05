"""
Test the retry functionality for crafting operations.

These tests verify that retrying a crafting action works correctly,
particularly focusing on state management issues where the item rarity
might not match the currency requirements.
"""

import pytest
from app.schemas.crafting import CraftableItem, ItemModifier, ModType
from app.services.crafting.simulator import CraftingSimulator

# Create a singleton simulator instance for all tests
simulator = CraftingSimulator()


@pytest.fixture
def magic_amulet():
    """Create a magic amulet with one prefix."""
    return CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity="Magic",
        item_level=75,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Healthy",
                mod_type=ModType.PREFIX,
                tier=3,
                stat_text="+{} to Maximum Life",
                stat_min=20,
                stat_max=29,
                current_value=25,
                mod_group="life",
                applicable_items=["amulet"],
                tags=["life"]
            )
        ],
        suffix_mods=[],
        implicit_mods=[],
        corrupted=False
    )


@pytest.fixture
def normal_amulet():
    """Create a normal amulet."""
    return CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity="Normal",
        item_level=75,
        quality=0,
        prefix_mods=[],
        suffix_mods=[],
        implicit_mods=[],
        corrupted=False
    )


def test_retry_regal_orb_on_magic_item(magic_amulet):
    """Test that retrying a Regal Orb on a magic item works correctly.

    This demonstrates the key retry behavior: we must apply the currency to the
    SAME starting state (the magic item), not to the result (the rare item).
    """
    # Make a copy since simulate_currency mutates the item
    from copy import deepcopy
    magic_copy1 = deepcopy(magic_amulet)
    magic_copy2 = deepcopy(magic_amulet)

    # Apply Regal Orb the first time
    result1 = simulator.simulate_currency(magic_copy1, "Regal Orb")
    assert result1.success is True
    rare_item = result1.result_item
    assert rare_item.rarity == "Rare"
    assert len(rare_item.prefix_mods) + len(rare_item.suffix_mods) == 2  # Started with 1, added 1

    # Retry: Apply Regal Orb to the ORIGINAL magic item again (not the rare result)
    result2 = simulator.simulate_currency(magic_copy2, "Regal Orb")
    assert result2.success is True
    rare_item2 = result2.result_item
    assert rare_item2.rarity == "Rare"
    assert len(rare_item2.prefix_mods) + len(rare_item2.suffix_mods) == 2

    # The two results should be different due to RNG
    # (unless we got extremely lucky and rolled the same mod)
    mod1_names = {mod.name for mod in rare_item.prefix_mods + rare_item.suffix_mods}
    mod2_names = {mod.name for mod in rare_item2.prefix_mods + rare_item2.suffix_mods}
    # We can't guarantee they're different, but they should both work


def test_retry_regal_orb_fails_on_rare_item(magic_amulet):
    """Test that Regal Orb fails when incorrectly applied to a Rare item."""
    # Apply Regal Orb to make it rare
    result1 = simulator.simulate_currency(magic_amulet, "Regal Orb")
    rare_item = result1.result_item
    assert rare_item.rarity == "Rare"

    # Try to apply Regal Orb to the Rare item (should fail)
    result2 = simulator.simulate_currency(rare_item, "Regal Orb")
    assert result2.success is False
    assert "Magic" in result2.message  # Error message should mention Magic items


def test_retry_transmutation_orb(normal_amulet):
    """Test that retrying a Transmutation Orb works correctly."""
    from copy import deepcopy
    normal_copy1 = deepcopy(normal_amulet)
    normal_copy2 = deepcopy(normal_amulet)

    # Apply Transmutation Orb the first time
    result1 = simulator.simulate_currency(normal_copy1, "Orb of Transmutation")
    assert result1.success is True
    magic_item1 = result1.result_item
    assert magic_item1.rarity == "Magic"
    assert 1 <= len(magic_item1.prefix_mods) + len(magic_item1.suffix_mods) <= 2

    # Retry: Apply Transmutation Orb to the ORIGINAL normal item again
    result2 = simulator.simulate_currency(normal_copy2, "Orb of Transmutation")
    assert result2.success is True
    magic_item2 = result2.result_item
    assert magic_item2.rarity == "Magic"
    assert 1 <= len(magic_item2.prefix_mods) + len(magic_item2.suffix_mods) <= 2


def test_retry_augmentation_orb(magic_amulet):
    """Test that retrying an Orb of Augmentation works correctly."""
    from copy import deepcopy

    # Create a magic item with only 1 mod (so augmentation can add another)
    magic_item_with_space = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity="Magic",
        item_level=75,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Healthy",
                mod_type=ModType.PREFIX,
                tier=3,
                stat_text="+{} to Maximum Life",
                stat_min=20,
                stat_max=29,
                current_value=25,
                mod_group="life",
                applicable_items=["amulet"],
                tags=["life"]
            )
        ],
        suffix_mods=[],
        implicit_mods=[],
        corrupted=False
    )

    magic_copy1 = deepcopy(magic_item_with_space)
    magic_copy2 = deepcopy(magic_item_with_space)

    # Apply Augmentation Orb the first time
    result1 = simulator.simulate_currency(magic_copy1, "Orb of Augmentation")
    assert result1.success is True
    magic_item1 = result1.result_item
    assert magic_item1.rarity == "Magic"
    assert len(magic_item1.prefix_mods) + len(magic_item1.suffix_mods) == 2

    # Retry: Apply Augmentation Orb to the ORIGINAL item again
    result2 = simulator.simulate_currency(magic_copy2, "Orb of Augmentation")
    assert result2.success is True
    magic_item2 = result2.result_item
    assert magic_item2.rarity == "Magic"
    assert len(magic_item2.prefix_mods) + len(magic_item2.suffix_mods) == 2


def test_retry_essence_on_magic_item():
    """Test that retrying an essence application works correctly.

    Note: In POE2, essences are applied to Magic items, not Normal items.
    """
    from copy import deepcopy

    # Create a fresh magic item with a different mod that won't conflict with Essence of the Body
    magic_item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity="Magic",
        item_level=75,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Dexterous",
                mod_type=ModType.PREFIX,
                tier=3,
                stat_text="+{} to Dexterity",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="dexterity",
                applicable_items=["amulet"],
                tags=["attribute"]
            )
        ],
        suffix_mods=[],
        implicit_mods=[],
        corrupted=False
    )

    magic_copy1 = deepcopy(magic_item)
    magic_copy2 = deepcopy(magic_item)

    # Apply Essence of the Body the first time (upgrades to Rare)
    result1 = simulator.simulate_currency(magic_copy1, "Essence of the Body")
    assert result1.success is True
    rare_item1 = result1.result_item
    assert rare_item1.rarity == "Rare"
    # Should have the essence mod plus the dexterity mod
    assert len(rare_item1.prefix_mods) + len(rare_item1.suffix_mods) >= 2

    # Retry: Apply the same essence to the ORIGINAL magic item again
    result2 = simulator.simulate_currency(magic_copy2, "Essence of the Body")
    assert result2.success is True
    rare_item2 = result2.result_item
    assert rare_item2.rarity == "Rare"
    assert len(rare_item2.prefix_mods) + len(rare_item2.suffix_mods) >= 2


def test_retry_essence_of_the_abyss():
    """Test that Essence of the Abyss can be applied successfully.

    Regression test for:
    1. AttributeError: 'EssenceInfo' object has no attribute 'tier' (fixed in unified_factory.py)
    2. "Mark of the Abyssal Lord not found in modifier pool" (fixed mod_group in modifiers.json)

    This test ensures the essence actually works, not just that config attributes exist.
    """
    from copy import deepcopy

    # Create a rare item for essence application (Essence of the Abyss requires Rare)
    rare_item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity="Rare",
        item_level=75,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Healthy",
                mod_type=ModType.PREFIX,
                tier=3,
                stat_text="+{} to Maximum Life",
                stat_min=20,
                stat_max=29,
                current_value=25,
                mod_group="life",
                applicable_items=["amulet"],
                tags=["life"]
            )
        ],
        suffix_mods=[
            ItemModifier(
                name="of the Magus",
                mod_type=ModType.SUFFIX,
                tier=2,
                stat_text="+{} to Maximum Mana",
                stat_min=30,
                stat_max=39,
                current_value=35,
                mod_group="mana",
                applicable_items=["amulet"],
                tags=["mana"]
            )
        ],
        implicit_mods=[],
        corrupted=False
    )

    rare_copy = deepcopy(rare_item)

    # Apply Essence of the Abyss - should succeed and add the "Abyssal" modifier
    result = simulator.simulate_currency(rare_copy, "Essence of the Abyss")
    assert result.success is True, f"Essence application failed: {result.message}"
    result_item = result.result_item
    assert result_item.rarity == "Rare"

    # Verify that the Abyssal mod was added
    all_mods = result_item.prefix_mods + result_item.suffix_mods
    abyssal_mods = [m for m in all_mods if m.name == "Abyssal"]
    assert len(abyssal_mods) == 1, "Expected 1 Abyssal modifier to be added"


def test_retry_preserves_omens(magic_amulet):
    """Test that retrying with omens works correctly (if omen system is implemented)."""
    # This test documents expected behavior with omens
    # For now, we just verify that the item state is correct
    # The retry should use the same omens as the original action
    # This is tested at the frontend level, but we verify the backend accepts it
    result = simulator.simulate_currency(magic_amulet, "Regal Orb")
    assert result.success is True


def test_regal_orb_randomizes_mod_type():
    """Test that Regal Orb randomly chooses between prefix and suffix.

    This test runs Regal Orb multiple times and verifies that we get
    both prefixes and suffixes, not just one type deterministically.
    """
    from copy import deepcopy

    # Create a magic item with 1 prefix, so we have room for both prefix and suffix
    magic_item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity="Magic",
        item_level=75,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Healthy",
                mod_type=ModType.PREFIX,
                tier=3,
                stat_text="+{} to Maximum Life",
                stat_min=20,
                stat_max=29,
                current_value=25,
                mod_group="life",
                applicable_items=["amulet"],
                tags=["life"]
            )
        ],
        suffix_mods=[],
        implicit_mods=[],
        corrupted=False
    )

    # Run Regal Orb 50 times and track what mod types were added
    prefix_added_count = 0
    suffix_added_count = 0

    for _ in range(50):
        test_item = deepcopy(magic_item)
        result = simulator.simulate_currency(test_item, "Regal Orb")
        assert result.success is True

        rare_item = result.result_item
        # The item started with 1 prefix, so check what was added
        if rare_item.prefix_count == 2:
            prefix_added_count += 1
        else:
            suffix_added_count += 1

    # With 50 trials, we should have gotten both types at least once
    # (probability of all 50 being the same type is (0.5)^50 ≈ 0)
    assert prefix_added_count > 0, "Regal Orb should sometimes add prefixes"
    assert suffix_added_count > 0, "Regal Orb should sometimes add suffixes"

    # Also verify it's roughly 50/50 (allow for some variance)
    # We expect around 25 each, but allow 15-35 range
    assert 15 <= prefix_added_count <= 35, f"Expected roughly 50/50 split, got {prefix_added_count} prefixes and {suffix_added_count} suffixes"
    assert 15 <= suffix_added_count <= 35, f"Expected roughly 50/50 split, got {prefix_added_count} prefixes and {suffix_added_count} suffixes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
