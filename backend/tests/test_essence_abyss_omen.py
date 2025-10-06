"""
Test Essence of the Abyss with Omens.

Tests that Mark of the Abyssal Lord chooses the correct affix type
based on available slots when used with crystallisation omens.
"""

import pytest
from app.schemas.crafting import CraftableItem, ItemRarity, ModType, OmenInfo, ItemModifier
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.modifier_loader import ModifierLoader
from app.services.crafting.mechanics import EssenceMechanic, OmenModifiedMechanic
from app.services.crafting.config_service import crafting_config_service


@pytest.fixture
def modifier_pool():
    """Load modifier pool from database."""
    modifiers = ModifierLoader.load_modifiers()
    return ModifierPool(modifiers)


@pytest.fixture
def essence_of_abyss():
    """Get Essence of the Abyss configuration."""
    essence_info = crafting_config_service.get_essence_config("Essence of the Abyss")
    assert essence_info is not None, "Essence of the Abyss not found"
    return essence_info


@pytest.fixture
def sinistral_crystallisation():
    """Get Omen of Sinistral Crystallisation."""
    return OmenInfo(
        id=1,
        name="Omen of Sinistral Crystallisation",
        effect_description="Perfect/Corrupted Essence removes only prefixes",
        affected_currency="Perfect Essence",
        effect_type="sinistral",
        stack_size=10,
        rules=[]
    )


def test_abyss_with_sinistral_adds_mark_as_prefix_when_suffixes_full(
    modifier_pool, essence_of_abyss, sinistral_crystallisation
):
    """
    Test: 1 prefix + 3 suffixes, Abyss + Sinistral Crystallisation

    Expected:
    1. Omen forces prefix removal
    2. Item becomes 0P + 3S
    3. Mark should be added as PREFIX (since suffixes are full)

    Actual bug reported by user:
    - Removed prefix (correct)
    - Also removed suffix (WRONG!)
    - Added Mark as suffix (WRONG!)
    """
    # Create item with 1P + 3S
    item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=81,
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
            ),
            ItemModifier(
                name="of Thunder",
                mod_type=ModType.SUFFIX,
                tier=5,
                stat_text="+10% to Lightning Resistance",
                stat_min=10,
                stat_max=15,
                current_value=12,
                mod_group="lightningresistance",
                tags=["resistance", "elemental"]
            )
        ],
        corrupted=False
    )

    # Apply Essence of Abyss with Sinistral Crystallisation omen
    base_essence = EssenceMechanic({}, essence_of_abyss)
    essence_with_omen = OmenModifiedMechanic(base_essence, sinistral_crystallisation)

    success, message, result_item = essence_with_omen.apply(item, modifier_pool)

    # Assertions
    assert success, f"Essence application failed: {message}"

    # Should have removed 1 prefix, added 0 prefixes (but Mark should be prefix)
    print(f"\nMessage: {message}")
    print(f"Original: 1P + 3S = {len(item.prefix_mods)}P + {len(item.suffix_mods)}S")
    print(f"Result:   {len(result_item.prefix_mods)}P + {len(result_item.suffix_mods)}S")
    print(f"Prefix mods: {[m.name for m in result_item.prefix_mods]}")
    print(f"Suffix mods: {[m.name for m in result_item.suffix_mods]}")

    # Expected result: Removed 1 prefix, added Mark as prefix (so 1P total with Mark)
    # Check that we have 1 prefix (the Mark replacing the removed prefix)
    assert len(result_item.prefix_mods) == 1, f"Expected 1 prefix (Mark replaced removed prefix), got {len(result_item.prefix_mods)}"

    # Check that NO suffixes were removed
    assert len(result_item.suffix_mods) == 3, f"Expected 3 suffixes (none removed), got {len(result_item.suffix_mods)}"

    # Check that the prefix is the Mark (modifier named "Abyssal" with stat_text "Bears the Mark of the Abyssal Lord")
    mark_in_prefixes = [m for m in result_item.prefix_mods if m.name == "Abyssal"]
    mark_in_suffixes = [m for m in result_item.suffix_mods if m.name == "Abyssal"]

    assert len(mark_in_prefixes) == 1, f"Expected Mark (Abyssal) as PREFIX, found {len(mark_in_prefixes)} in prefixes"
    assert len(mark_in_suffixes) == 0, f"Expected no Mark in suffixes, found {len(mark_in_suffixes)}"

    print(f"✓ Test PASSED: Mark correctly added as PREFIX when suffixes are full")


def test_abyss_with_dextral_adds_mark_as_suffix_when_prefixes_full(
    modifier_pool, essence_of_abyss
):
    """
    Test: 3 prefixes + 1 suffix, Abyss + Dextral Crystallisation

    Expected:
    1. Omen forces suffix removal
    2. Item becomes 3P + 0S
    3. Mark should be added as SUFFIX (since prefixes are full)
    """
    dextral_omen = OmenInfo(
        id=2,
        name="Omen of Dextral Crystallisation",
        effect_description="Perfect/Corrupted Essence removes only suffixes",
        affected_currency="Perfect Essence",
        effect_type="dextral",
        stack_size=10,
        rules=[]
    )

    # Create item with 3P + 1S
    item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=81,
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
            ),
            ItemModifier(
                name="Robust",
                mod_type=ModType.PREFIX,
                tier=6,
                stat_text="+35 to maximum Life",
                stat_min=31,
                stat_max=39,
                current_value=35,
                mod_group="life",
                tags=["life"]
            ),
            ItemModifier(
                name="Healthy",
                mod_type=ModType.PREFIX,
                tier=5,
                stat_text="+43 to maximum Life",
                stat_min=40,
                stat_max=49,
                current_value=43,
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
            )
        ],
        corrupted=False
    )

    # Apply Essence of Abyss with Dextral Crystallisation omen
    base_essence = EssenceMechanic({}, essence_of_abyss)
    essence_with_omen = OmenModifiedMechanic(base_essence, dextral_omen)

    success, message, result_item = essence_with_omen.apply(item, modifier_pool)

    # Assertions
    assert success, f"Essence application failed: {message}"

    print(f"\nMessage: {message}")
    print(f"Original: 3P + 1S")
    print(f"Result:   {len(result_item.prefix_mods)}P + {len(result_item.suffix_mods)}S")
    print(f"Prefix mods: {[m.name for m in result_item.prefix_mods]}")
    print(f"Suffix mods: {[m.name for m in result_item.suffix_mods]}")

    # Check that NO prefixes were removed
    assert len(result_item.prefix_mods) == 3, f"Expected 3 prefixes (none removed), got {len(result_item.prefix_mods)}"

    # Expected result: Removed 1 suffix, added Mark as suffix (so 1S total with Mark)
    assert len(result_item.suffix_mods) == 1, f"Expected 1 suffix (Mark replaced removed suffix), got {len(result_item.suffix_mods)}"

    # Check that the suffix is the Mark (modifier named "Abyssal" with stat_text "Bears the Mark of the Abyssal Lord")
    mark_in_prefixes = [m for m in result_item.prefix_mods if m.name == "Abyssal"]
    mark_in_suffixes = [m for m in result_item.suffix_mods if m.name == "Abyssal"]

    assert len(mark_in_suffixes) == 1, f"Expected Mark (Abyssal) as SUFFIX, found {len(mark_in_suffixes)} in suffixes"
    assert len(mark_in_prefixes) == 0, f"Expected no Mark in prefixes, found {len(mark_in_prefixes)}"

    print(f"✓ Test PASSED: Mark correctly added as SUFFIX when prefixes are full")
