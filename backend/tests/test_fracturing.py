"""
Comprehensive tests for Orb of Fracturing mechanics.

Tests:
1. Fracturing requires Rare items
2. Fracturing requires 4+ explicit mods
3. Mark of Abyssal Lord CAN be fractured
4. Unrevealed desecrated modifiers CANNOT be fractured
5. Fractured mods cannot be removed by Chaos Orb
6. Fractured mods cannot be removed by Annulment
7. Fractured mods cannot be removed by Desecration
8. Fractured mods cannot be removed by Omens
9. Divine Orb can still reroll fractured mod values
10. Cannot fracture an already fractured item
11. Fracturing protection across all removal mechanics
"""

import pytest
from app.schemas.crafting import CraftableItem, ItemRarity, ModType, ItemModifier
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.modifier_loader import ModifierLoader
from app.services.crafting.mechanics import (
    FracturingMechanic, ChaosMechanic, AnnulmentMechanic, DivineMechanic, DesecrationMechanic
)
from app.services.crafting.omens import OmenOfWhittling, OmenOfSinistralErasure
from app.services.crafting.config_service import crafting_config_service


@pytest.fixture
def modifier_pool():
    """Load modifier pool from database."""
    modifiers = ModifierLoader.load_modifiers()
    return ModifierPool(modifiers)


@pytest.fixture
def rare_item_4_mods():
    """Create a rare item with 4 mods (2 prefix, 2 suffix)."""
    return CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=75,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Sturdy",
                mod_type=ModType.PREFIX,
                tier=7,
                stat_text="+26 to maximum Life",
                stat_min=26,
                stat_max=30,
                current_value=28,
                mod_group="life",
                tags=["life"],
                is_fractured=False
            ),
            ItemModifier(
                name="Vigorous",
                mod_type=ModType.PREFIX,
                tier=5,
                stat_text="+40 to maximum Life",
                stat_min=35,
                stat_max=45,
                current_value=40,
                mod_group="life2",
                tags=["life"],
                is_fractured=False
            )
        ],
        suffix_mods=[
            ItemModifier(
                name="of Fire",
                mod_type=ModType.SUFFIX,
                tier=5,
                stat_text="+10% to Fire Resistance",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="fireresistance",
                tags=["resistance", "elemental"],
                is_fractured=False
            ),
            ItemModifier(
                name="of Ice",
                mod_type=ModType.SUFFIX,
                tier=5,
                stat_text="+10% to Cold Resistance",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="coldresistance",
                tags=["resistance", "elemental"],
                is_fractured=False
            )
        ],
        corrupted=False
    )


def test_fracturing_requires_rare_item(modifier_pool):
    """Test that Orb of Fracturing requires a Rare item."""
    magic_item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.MAGIC,
        item_level=75,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Sturdy",
                mod_type=ModType.PREFIX,
                tier=7,
                stat_text="+26 to maximum Life",
                stat_min=26,
                stat_max=30,
                current_value=28,
                mod_group="life",
                tags=["life"]
            )
        ],
        suffix_mods=[],
        corrupted=False
    )

    mechanic = FracturingMechanic(config={})
    can_apply, error = mechanic.can_apply(magic_item)

    assert not can_apply
    assert "Rare" in error


def test_fracturing_requires_4_mods(modifier_pool):
    """Test that Orb of Fracturing requires at least 4 explicit mods."""
    rare_item_3_mods = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=75,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Sturdy",
                mod_type=ModType.PREFIX,
                tier=7,
                stat_text="+26 to maximum Life",
                stat_min=26,
                stat_max=30,
                current_value=28,
                mod_group="life",
                tags=["life"]
            )
        ],
        suffix_mods=[
            ItemModifier(
                name="of Fire",
                mod_type=ModType.SUFFIX,
                tier=5,
                stat_text="+10% to Fire Resistance",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="fireresistance",
                tags=["resistance", "elemental"]
            ),
            ItemModifier(
                name="of Ice",
                mod_type=ModType.SUFFIX,
                tier=5,
                stat_text="+10% to Cold Resistance",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="coldresistance",
                tags=["resistance", "elemental"]
            )
        ],
        corrupted=False
    )

    mechanic = FracturingMechanic(config={})
    can_apply, error = mechanic.can_apply(rare_item_3_mods)

    assert not can_apply
    assert "at least 4" in error


def test_fracturing_succeeds_on_valid_item(modifier_pool, rare_item_4_mods):
    """Test that fracturing succeeds on a valid rare item with 4+ mods."""
    mechanic = FracturingMechanic(config={})
    success, message, result_item = mechanic.apply(rare_item_4_mods, modifier_pool)

    assert success
    assert "Fractured" in message

    # Check that exactly one mod is fractured
    all_mods = result_item.prefix_mods + result_item.suffix_mods
    fractured_mods = [mod for mod in all_mods if mod.is_fractured]
    assert len(fractured_mods) == 1


def test_mark_of_abyssal_lord_can_be_fractured(modifier_pool):
    """Test that Mark of the Abyssal Lord CAN be fractured."""
    item_with_mark = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=81,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Abyssal",
                mod_type=ModType.PREFIX,
                tier=0,
                stat_text="Bears the Mark of the Abyssal Lord",
                mod_group="abyssal_mark",
                tags=["abyssal"],
                is_fractured=False
            ),
            ItemModifier(
                name="Sturdy",
                mod_type=ModType.PREFIX,
                tier=7,
                stat_text="+26 to maximum Life",
                stat_min=26,
                stat_max=30,
                current_value=28,
                mod_group="life",
                tags=["life"],
                is_fractured=False
            )
        ],
        suffix_mods=[
            ItemModifier(
                name="of Fire",
                mod_type=ModType.SUFFIX,
                tier=5,
                stat_text="+10% to Fire Resistance",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="fireresistance",
                tags=["resistance", "elemental"],
                is_fractured=False
            ),
            ItemModifier(
                name="of Ice",
                mod_type=ModType.SUFFIX,
                tier=5,
                stat_text="+10% to Cold Resistance",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="coldresistance",
                tags=["resistance", "elemental"],
                is_fractured=False
            )
        ],
        corrupted=False
    )

    mechanic = FracturingMechanic(config={})
    success, message, result_item = mechanic.apply(item_with_mark, modifier_pool)

    assert success

    # Check that exactly one mod is fractured (Mark can be one of them)
    all_mods = result_item.prefix_mods + result_item.suffix_mods
    fractured_mods = [mod for mod in all_mods if mod.is_fractured]
    assert len(fractured_mods) == 1


def test_chaos_orb_cannot_remove_fractured_mods(modifier_pool, rare_item_4_mods):
    """Test that Chaos Orb cannot remove fractured mods."""
    # Fracture one mod
    rare_item_4_mods.prefix_mods[0].is_fractured = True
    fractured_mod_name = rare_item_4_mods.prefix_mods[0].name

    mechanic = ChaosMechanic(config={})
    success, message, result_item = mechanic.apply(rare_item_4_mods, modifier_pool)

    assert success

    # The fractured mod should still be present
    fractured_mod_still_present = any(
        mod.name == fractured_mod_name and mod.is_fractured
        for mod in result_item.prefix_mods
    )
    assert fractured_mod_still_present


def test_annulment_cannot_remove_fractured_mods(modifier_pool, rare_item_4_mods):
    """Test that Orb of Annulment cannot remove fractured mods."""
    # Fracture one mod
    rare_item_4_mods.suffix_mods[0].is_fractured = True
    fractured_mod_name = rare_item_4_mods.suffix_mods[0].name

    mechanic = AnnulmentMechanic(config={})
    success, message, result_item = mechanic.apply(rare_item_4_mods, modifier_pool)

    assert success

    # The fractured mod should still be present
    fractured_mod_still_present = any(
        mod.name == fractured_mod_name and mod.is_fractured
        for mod in result_item.suffix_mods
    )
    assert fractured_mod_still_present


def test_annulment_fails_when_all_mods_fractured(modifier_pool, rare_item_4_mods):
    """Test that Annulment fails when all mods are fractured."""
    # Fracture all mods
    for mod in rare_item_4_mods.prefix_mods:
        mod.is_fractured = True
    for mod in rare_item_4_mods.suffix_mods:
        mod.is_fractured = True

    mechanic = AnnulmentMechanic(config={})
    success, message, result_item = mechanic.apply(rare_item_4_mods, modifier_pool)

    assert not success
    assert "fractured" in message.lower()


def test_divine_orb_rerolls_fractured_mod_values(modifier_pool, rare_item_4_mods):
    """Test that Divine Orb can still reroll fractured mod values."""
    # Fracture one mod and note its value
    rare_item_4_mods.prefix_mods[0].is_fractured = True
    original_value = rare_item_4_mods.prefix_mods[0].current_value

    mechanic = DivineMechanic(config={})
    success, message, result_item = mechanic.apply(rare_item_4_mods, modifier_pool)

    assert success

    # The fractured mod should still be fractured
    fractured_mod = result_item.prefix_mods[0]
    assert fractured_mod.is_fractured

    # Value might have changed (Divine rerolls values)
    # We can't assert it changed because random might give same value,
    # but we can assert it's within the valid range
    assert fractured_mod.stat_min <= fractured_mod.current_value <= fractured_mod.stat_max


def test_cannot_fracture_already_fractured_item(modifier_pool, rare_item_4_mods):
    """Test that you cannot fracture an item that already has a fractured mod."""
    # Fracture one mod
    rare_item_4_mods.prefix_mods[0].is_fractured = True

    mechanic = FracturingMechanic(config={})
    can_apply, error = mechanic.can_apply(rare_item_4_mods)

    assert not can_apply
    assert "already has a fractured modifier" in error


def test_omen_of_whittling_respects_fractured_mods(modifier_pool, rare_item_4_mods):
    """Test that Omen of Whittling cannot remove fractured mods."""
    # Set one mod as fractured and make it the lowest level
    rare_item_4_mods.prefix_mods[0].is_fractured = True
    rare_item_4_mods.prefix_mods[0].required_ilvl = 1

    # Set other mods to higher ilvl
    rare_item_4_mods.prefix_mods[1].required_ilvl = 50
    rare_item_4_mods.suffix_mods[0].required_ilvl = 50
    rare_item_4_mods.suffix_mods[1].required_ilvl = 50

    omen = OmenOfWhittling()

    # Create a mock currency function that would normally add a mod
    def mock_currency_func(item, mod_pool):
        # Just return success without actually modifying
        return True, "Applied mock currency", item

    success, message, result_item = omen.modify_currency_behavior(
        rare_item_4_mods, mock_currency_func, modifier_pool
    )

    assert success

    # The fractured lowest-level mod should still be present
    fractured_mod_still_present = any(
        mod.is_fractured and mod.required_ilvl == 1
        for mod in result_item.prefix_mods
    )
    assert fractured_mod_still_present


def test_omen_of_sinistral_erasure_respects_fractured_prefixes(modifier_pool, rare_item_4_mods):
    """Test that Omen of Sinistral Erasure cannot remove fractured prefixes."""
    # Fracture both prefixes
    rare_item_4_mods.prefix_mods[0].is_fractured = True
    rare_item_4_mods.prefix_mods[1].is_fractured = True

    omen = OmenOfSinistralErasure()

    def mock_currency_func(item, mod_pool):
        return True, "Applied mock currency", item

    success, message, result_item = omen.modify_currency_behavior(
        rare_item_4_mods, mock_currency_func, modifier_pool
    )

    # Should fail because no non-fractured prefixes available
    assert not success
    assert "fractured" in message.lower()


def test_desecration_respects_fractured_mods(modifier_pool, rare_item_4_mods):
    """Test that Desecration mechanics cannot remove fractured mods."""
    # Fracture one mod
    rare_item_4_mods.prefix_mods[0].is_fractured = True
    fractured_mod_name = rare_item_4_mods.prefix_mods[0].name

    # Get a bone config (use Ancient Collarbone - no max level restriction)
    bone_info = crafting_config_service.get_bone_config("Ancient Collarbone")
    if bone_info is None:
        pytest.skip("Ancient Collarbone config not found")

    # Create config from bone_info
    config = {
        'bone_type': bone_info.bone_type,
        'bone_part': bone_info.bone_part,
        'max_item_level': bone_info.max_item_level,
        'min_modifier_level': bone_info.min_modifier_level
    }

    mechanic = DesecrationMechanic(config=config)
    success, message, result_item = mechanic.apply(rare_item_4_mods, modifier_pool)

    # Desecration should still work
    assert success

    # The fractured mod should still be present and fractured
    fractured_mod_still_present = any(
        mod.name == fractured_mod_name and mod.is_fractured
        for mod in result_item.prefix_mods
    )
    assert fractured_mod_still_present


def test_unrevealed_mods_cannot_be_fractured(modifier_pool):
    """Test that unrevealed desecrated modifiers cannot be fractured."""
    item_with_unrevealed = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=81,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Hidden Modifier",
                mod_type=ModType.PREFIX,
                tier=0,
                stat_text="???",
                mod_group="unrevealed",
                tags=["desecrated"],
                is_unrevealed=True,
                is_fractured=False
            ),
            ItemModifier(
                name="Sturdy",
                mod_type=ModType.PREFIX,
                tier=7,
                stat_text="+26 to maximum Life",
                stat_min=26,
                stat_max=30,
                current_value=28,
                mod_group="life",
                tags=["life"],
                is_fractured=False
            )
        ],
        suffix_mods=[
            ItemModifier(
                name="of Fire",
                mod_type=ModType.SUFFIX,
                tier=5,
                stat_text="+10% to Fire Resistance",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="fireresistance",
                tags=["resistance", "elemental"],
                is_fractured=False
            ),
            ItemModifier(
                name="of Ice",
                mod_type=ModType.SUFFIX,
                tier=5,
                stat_text="+10% to Cold Resistance",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="coldresistance",
                tags=["resistance", "elemental"],
                is_fractured=False
            )
        ],
        corrupted=False
    )

    mechanic = FracturingMechanic(config={})
    success, message, result_item = mechanic.apply(item_with_unrevealed, modifier_pool)

    assert success

    # Check that the unrevealed mod was NOT fractured
    unrevealed_mod = next((mod for mod in result_item.prefix_mods if mod.is_unrevealed), None)
    assert unrevealed_mod is not None
    assert not unrevealed_mod.is_fractured

    # Check that one of the other mods was fractured
    all_mods = result_item.prefix_mods + result_item.suffix_mods
    fractured_mods = [mod for mod in all_mods if mod.is_fractured]
    assert len(fractured_mods) == 1
    assert not fractured_mods[0].is_unrevealed
