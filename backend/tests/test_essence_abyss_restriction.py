"""
Test Essence of the Abyss restriction: cannot be used on items with desecrated mods.
"""

import pytest
from app.schemas.crafting import CraftableItem, ItemModifier, ModType, ItemRarity
from app.services.crafting.simulator import CraftingSimulator

# Create a singleton simulator instance for all tests
simulator = CraftingSimulator()


def test_essence_abyss_blocked_on_desecrated_item():
    """Test that Essence of the Abyss cannot be used on items with desecrated mods."""
    # Create a Rare item with a desecrated modifier
    item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=81,
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
            ),
            ItemModifier(
                name="Desecrated Life Mod",
                mod_type=ModType.PREFIX,
                tier=1,
                stat_text="+{} to Maximum Life (Desecrated)",
                stat_min=100,
                stat_max=150,
                current_value=125,
                mod_group="life_desecrated",
                applicable_items=["amulet"],
                tags=["life", "desecrated_only"],
                is_desecrated=True
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
        corrupted=False
    )

    # Try to apply Essence of the Abyss
    result = simulator.simulate_currency(item, "Essence of the Abyss")

    # Should fail with appropriate message
    assert result.success is False, "Essence of the Abyss should not work on items with desecrated mods"
    assert "Desecrated modifiers" in result.message, f"Expected error about desecrated mods, got: {result.message}"


def test_essence_abyss_allowed_on_non_desecrated_item():
    """Test that Essence of the Abyss works normally on items without desecrated mods."""
    # Create a Rare item WITHOUT desecrated modifiers
    item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=81,
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
        corrupted=False
    )

    # Apply Essence of the Abyss
    result = simulator.simulate_currency(item, "Essence of the Abyss")

    # Should succeed
    assert result.success is True, f"Essence of the Abyss should work on non-desecrated items: {result.message}"

    # Verify the Abyssal mark was added
    all_mods = result.result_item.prefix_mods + result.result_item.suffix_mods
    abyssal_mods = [m for m in all_mods if m.name == "Abyssal"]
    assert len(abyssal_mods) == 1, "Expected Abyssal modifier to be added"


def test_essence_abyss_blocked_on_item_with_mark():
    """Test that Essence of the Abyss cannot be used on items that already have Mark of the Abyssal Lord."""
    # Create a Rare item with the Abyssal mark (from a previous Essence of the Abyss use)
    item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=81,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Abyssal",
                mod_type=ModType.PREFIX,
                tier=1,
                stat_text="Bears the Mark of the Abyssal Lord",
                stat_min=1,
                stat_max=1,
                current_value=1,
                mod_group="abyssal_mark",
                applicable_items=["amulet"],
                tags=["abyssal_mark"]
            ),
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
        corrupted=False
    )

    # Try to apply Essence of the Abyss again
    result = simulator.simulate_currency(item, "Essence of the Abyss")

    # Should fail with appropriate message
    assert result.success is False, "Essence of the Abyss should not work on items that already have the Mark"
    assert "Mark of the Abyssal Lord" in result.message, f"Expected error about Mark of the Abyssal Lord, got: {result.message}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
