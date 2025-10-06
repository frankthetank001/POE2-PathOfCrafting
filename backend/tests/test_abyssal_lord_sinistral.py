"""
Test for Essence of the Abyssal Lord with Omen of Sinistral Crystallisation bug.

Bug Report:
- Item: 2P + 3S (prefixes and suffixes full)
- Currency: Essence of the Abyssal Lord
- Omen: Omen of Sinistral Crystallisation (removes a prefix)
- Expected: Remove 1 prefix, add essence mod as prefix (since suffixes are full)
- Actual: Either removes prefix without adding mod, OR removes prefix AND suffix to add mod as suffix
"""
import pytest
from app.services.crafting.simulator import CraftingSimulator
from app.schemas.crafting import CraftableItem, ItemModifier


def test_essence_abyssal_lord_with_sinistral_crystallisation():
    """
    Test that Essence of the Abyss with Omen of Sinistral Crystallisation works correctly.

    The omen controls which mod type is REMOVED (prefix in this case).
    Mark placement is based on available slots ONLY:
    - Start: 2P + 3S (suffixes are full)
    - Omen removes prefix: 1P + 3S (only prefix slot available)
    - Mark goes to prefix (only available slot)
    """

    # Create the item from the bug report
    # Item has 2 prefixes and 3 suffixes (suffixes are full)
    item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity="Rare",
        item_level=81,
        quality=0,
        implicit_mods=[],
        prefix_mods=[
            ItemModifier(
                name="Occultist's",
                mod_type="prefix",
                tier=2,
                stat_text="+24% to Spell Damage",
                stat_min=23,
                stat_max=26,
                current_value=24,
                mod_group="SpellDamage",
                tags=["damage", "caster"]
            ),
            ItemModifier(
                name="Deliberate",
                mod_type="prefix",
                tier=5,
                stat_text="+111 to Accuracy Rating",
                stat_min=85,
                stat_max=123,
                current_value=111,
                mod_group="AccuracyRating",
                tags=["attack"]
            )
        ],
        suffix_mods=[
            ItemModifier(
                name="of the Sorcerer",
                mod_type="suffix",
                tier=1,
                stat_text="+3 to Level of all Spell Skills",
                stat_min=3,
                stat_max=3,
                current_value=3,
                mod_group="SkillLevels",
                tags=["caster", "gem"]
            ),
            ItemModifier(
                name="of Ferocity",
                mod_type="suffix",
                tier=1,
                stat_text="+31% to Critical Damage Bonus",
                stat_min=30,
                stat_max=34,
                current_value=31,
                mod_group="CriticalDamageBonus",
                tags=["damage", "critical"]
            ),
            ItemModifier(
                name="of Legerdemain",
                mod_type="suffix",
                tier=1,
                stat_text="+27% to Cast Speed",
                stat_min=25,
                stat_max=28,
                current_value=27,
                mod_group="CastSpeed",
                tags=["caster", "speed"]
            )
        ],
        unrevealed_mods=[],
        corrupted=False,
        base_stats={},
        calculated_stats={}
    )

    # Apply Essence of the Abyss with Omen of Sinistral Crystallisation
    simulator = CraftingSimulator()
    result = simulator.simulate_currency_with_omens(
        item=item,
        currency_name="Essence of the Abyss",
        omen_names=["Omen of Sinistral Crystallisation"]
    )

    print("\n=== Test Result ===")
    print(f"Success: {result.success}")
    print(f"Message: {result.message}")

    assert result.success, f"Crafting should succeed: {result.message}"
    assert result.result_item is not None, "Result item should not be None"

    item = result.result_item
    print(f"Item rarity: {item.rarity}")
    print(f"Prefixes: {len(item.prefix_mods)}")
    print(f"Suffixes: {len(item.suffix_mods)}")
    print("\nPrefix mods:")
    for mod in item.prefix_mods:
        print(f"  - {mod.name}: {mod.stat_text}")
    print("\nSuffix mods:")
    for mod in item.suffix_mods:
        print(f"  - {mod.name}: {mod.stat_text}")

    # Assertions
    # After using the essence with the omen:
    # 1. Should remove 1 prefix (2 -> 1)
    # 2. Should add essence mod as a prefix (1 -> 2)
    # 3. Suffixes should remain full (3)

    assert item.rarity.value == 'Rare', "Item should remain rare"

    # Check that we have 2 prefixes (1 remaining + 1 essence mod)
    assert len(item.prefix_mods) == 2, \
        f"Expected 2 prefixes after removing 1 and adding essence mod, got {len(item.prefix_mods)}"

    # Check that suffixes are still full (should not have been touched)
    assert len(item.suffix_mods) == 3, \
        f"Expected 3 suffixes (unchanged), got {len(item.suffix_mods)}"

    # Check that one of the mods (prefix or suffix) is the essence mod
    # The essence mod can be in either position based on available slots
    # Check by mod_group since the name can vary ("Abyssal", "Mark of the Abyssal Lord", etc.)
    all_mods = item.prefix_mods + item.suffix_mods
    has_essence_mod = any(mod.mod_group == "abyssal_mark" for mod in all_mods)

    all_mod_info = [f"{mod.name} (group: {mod.mod_group})" for mod in all_mods]
    assert has_essence_mod, \
        f"Expected essence mod (abyssal_mark group) in either prefix or suffix, but mods are: {all_mod_info}"


def test_desecration_replaces_mark_of_abyssal_lord():
    """
    Test that desecration (bones) correctly replaces Mark of the Abyssal Lord.
    The Mark should be replaced with an unrevealed desecrated modifier of the same type.
    """
    # First, create an item with Mark of the Abyssal Lord as a prefix
    # Use Essence of Abyss with Sinistral Crystallisation on 2P+3S item
    item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity="Rare",
        item_level=81,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="Occultist's",
                mod_type="prefix",
                tier=2,
                stat_text="+24% to Spell Damage",
                stat_min=23,
                stat_max=26,
                current_value=24,
                mod_group="SpellDamage",
                tags=["damage", "caster"]
            ),
            ItemModifier(
                name="Deliberate",
                mod_type="prefix",
                tier=5,
                stat_text="+111 to Accuracy Rating",
                stat_min=85,
                stat_max=123,
                current_value=111,
                mod_group="AccuracyRating",
                tags=["attack"]
            )
        ],
        suffix_mods=[
            ItemModifier(
                name="of the Sorcerer",
                mod_type="suffix",
                tier=1,
                stat_text="+3 to Level of all Spell Skills",
                stat_min=3,
                stat_max=3,
                current_value=3,
                mod_group="SkillLevels",
                tags=["caster", "gem"]
            ),
            ItemModifier(
                name="of Ferocity",
                mod_type="suffix",
                tier=1,
                stat_text="+31% to Critical Damage Bonus",
                stat_min=30,
                stat_max=34,
                current_value=31,
                mod_group="CriticalDamageBonus",
                tags=["damage", "critical"]
            ),
            ItemModifier(
                name="of Legerdemain",
                mod_type="suffix",
                tier=1,
                stat_text="+27% to Cast Speed",
                stat_min=25,
                stat_max=28,
                current_value=27,
                mod_group="CastSpeed",
                tags=["caster", "speed"]
            )
        ],
        unrevealed_mods=[],
        corrupted=False,
        base_stats={},
        calculated_stats={}
    )

    # Apply Essence of the Abyss with Sinistral Crystallisation
    simulator = CraftingSimulator()
    result1 = simulator.simulate_currency_with_omens(
        item=item,
        currency_name="Essence of the Abyss",
        omen_names=["Omen of Sinistral Crystallisation"]
    )

    assert result1.success, f"Essence should succeed: {result1.message}"
    assert result1.result_item is not None

    # Verify Mark was added as prefix
    mark_in_prefixes = any(
        mod.mod_group == "abyssal_mark" for mod in result1.result_item.prefix_mods
    )
    assert mark_in_prefixes, "Mark of the Abyssal Lord should be in prefixes"

    # Now apply desecration (Ancient Collarbone) to replace the Mark
    result2 = simulator.simulate_currency(
        item=result1.result_item,
        currency_name="Ancient Collarbone"
    )

    assert result2.success, f"Desecration should succeed: {result2.message}"
    assert result2.result_item is not None
    assert "Replaced Mark of the Abyssal Lord" in result2.message

    # Verify Mark was replaced with unrevealed desecrated modifier
    item2 = result2.result_item
    mark_still_present = any(
        mod.mod_group == "abyssal_mark"
        for mod in item2.prefix_mods + item2.suffix_mods
    )
    assert not mark_still_present, "Mark should be replaced, not present anymore"

    # Verify unrevealed modifier was added
    unrevealed_in_prefixes = any(
        mod.is_unrevealed for mod in item2.prefix_mods
    )
    assert unrevealed_in_prefixes, "Unrevealed modifier should be in prefixes (same type as Mark)"

    # Verify unrevealed_mods metadata
    assert len(item2.unrevealed_mods) == 1, f"Should have 1 unrevealed mod metadata, got {len(item2.unrevealed_mods)}"
    assert item2.unrevealed_mods[0].mod_type.value == "prefix", "Unrevealed mod should be prefix (same as Mark)"


def test_mark_placement_random_when_both_slots_available():
    """
    Test that Mark of the Abyssal Lord is placed randomly when both prefix and suffix slots are available.

    The omen controls what is REMOVED, not where Mark goes.
    - Start: 1P + 2S (both have room)
    - Omen removes prefix: 0P + 2S (both still have room)
    - Mark goes to random slot (could be prefix or suffix)
    """
    import random

    # Set seed for deterministic test
    random.seed(42)

    item = CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity="Rare",
        item_level=81,
        quality=0,
        prefix_mods=[
            ItemModifier(
                name="TestPrefix",
                mod_type="prefix",
                tier=1,
                stat_text="+10 Test",
                stat_min=10,
                stat_max=10,
                current_value=10,
                mod_group="TestGroup1",
                tags=["test"]
            )
        ],
        suffix_mods=[
            ItemModifier(
                name="TestSuffix1",
                mod_type="suffix",
                tier=1,
                stat_text="+20 Test",
                stat_min=20,
                stat_max=20,
                current_value=20,
                mod_group="TestGroup2",
                tags=["test"]
            ),
            ItemModifier(
                name="TestSuffix2",
                mod_type="suffix",
                tier=1,
                stat_text="+30 Test",
                stat_min=30,
                stat_max=30,
                current_value=30,
                mod_group="TestGroup3",
                tags=["test"]
            )
        ],
        unrevealed_mods=[],
        corrupted=False,
        base_stats={},
        calculated_stats={}
    )

    simulator = CraftingSimulator()
    result = simulator.simulate_currency_with_omens(
        item=item,
        currency_name="Essence of the Abyss",
        omen_names=["Omen of Sinistral Crystallisation"]
    )

    assert result.success, f"Should succeed: {result.message}"
    assert result.result_item is not None

    # Verify Mark was added
    all_mods = result.result_item.prefix_mods + result.result_item.suffix_mods
    has_mark = any(mod.mod_group == "abyssal_mark" for mod in all_mods)
    assert has_mark, "Mark should be added to either prefix or suffix"

    # Verify total mod count is correct (started with 3, removed 1, added 1 = 3)
    total_mods = len(result.result_item.prefix_mods) + len(result.result_item.suffix_mods)
    assert total_mods == 3, f"Should have 3 total mods, got {total_mods}"


if __name__ == "__main__":
    test_essence_abyssal_lord_with_sinistral_crystallisation()
    test_desecration_replaces_mark_of_abyssal_lord()
    test_mark_placement_random_when_both_slots_available()
