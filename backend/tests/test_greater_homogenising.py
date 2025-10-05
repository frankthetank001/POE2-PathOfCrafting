"""
Test Greater + Homogenising Exaltation mechanics.

Ensures that Greater Exaltation + Homogenising correctly:
1. Collects ALL tags from ALL existing mods
2. Searches both prefix and suffix pools
3. Adds 2 mods with matching tags
"""

import pytest
from app.schemas.crafting import CraftableItem, ItemRarity, ModType, OmenInfo
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.modifier_loader import ModifierLoader
from app.services.crafting.mechanics import ExaltedMechanic, OmenModifiedMechanic


@pytest.fixture
def modifier_pool():
    """Load modifier pool from database."""
    modifiers = ModifierLoader.load_modifiers()
    return ModifierPool(modifiers)


@pytest.fixture
def test_item_with_mixed_tags(modifier_pool):
    """
    Create rare amulet with:
    - Deliberate prefix (attack tag)
    - Occultist's prefix (caster_damage, damage, caster tags)
    - Sorcerer suffix (caster, gem tags)
    """
    deliberate = next(
        (m for m in modifier_pool.modifiers
         if m.name == "Deliberate"
         and m.tier == 5
         and "amulet" in m.applicable_items),
        None
    )
    assert deliberate is not None, "Deliberate not found"

    occultist = next(
        (m for m in modifier_pool.modifiers
         if m.name == "Occultist's"
         and m.tier == 2
         and "amulet" in m.applicable_items),
        None
    )
    assert occultist is not None, "Occultist's not found"

    sorcerer = next(
        (m for m in modifier_pool.modifiers
         if "Level of all Spell Skills" in m.stat_text
         and m.mod_type == ModType.SUFFIX
         and "amulet" in m.applicable_items),
        None
    )
    assert sorcerer is not None, "Sorcerer not found"

    return CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.RARE,
        item_level=81,
        quality=0,
        prefix_mods=[
            deliberate.model_copy(deep=True),
            occultist.model_copy(deep=True)
        ],
        suffix_mods=[
            sorcerer.model_copy(deep=True)
        ],
        corrupted=False
    )


def test_greater_homogenising_uses_all_tags(test_item_with_mixed_tags, modifier_pool):
    """
    Test that Greater + Homogenising collects ALL tags from ALL mods.

    Item has:
    - attack tag (from Deliberate)
    - caster_damage, damage, caster tags (from Occultist's)
    - caster, gem tags (from Sorcerer)

    Should be able to add mods matching ANY of these tags.
    Expected mods: Cast Speed (caster), Critical Damage Bonus (damage), etc.
    """
    # Create omens
    homogenising_omen = OmenInfo(
        id=1,
        name="Omen of Homogenising Exaltation",
        effect_description="Exalted adds matching tags",
        affected_currency="Exalted Orb",
        effect_type="homogenising",
        stack_size=10,
        rules=[]
    )

    greater_omen = OmenInfo(
        id=2,
        name="Omen of Greater Exaltation",
        effect_description="Exalted adds 2 mods",
        affected_currency="Exalted Orb",
        effect_type="greater",
        stack_size=10,
        rules=[]
    )

    config = {}
    base_exalted = ExaltedMechanic(config)
    exalted_with_homog = OmenModifiedMechanic(base_exalted, homogenising_omen)
    exalted_with_both = OmenModifiedMechanic(exalted_with_homog, greater_omen)

    # Run 30 tests
    successes = 0
    added_mods = []

    for i in range(30):
        test_item_copy = test_item_with_mixed_tags.model_copy(deep=True)
        success, message, result_item = exalted_with_both.apply(test_item_copy, modifier_pool)

        if success:
            successes += 1
            # Count mods added
            total_mods = len(result_item.prefix_mods) + len(result_item.suffix_mods)
            original_mods = len(test_item_with_mixed_tags.prefix_mods) + len(test_item_with_mixed_tags.suffix_mods)
            mods_added = total_mods - original_mods

            # Find what was added
            for p in result_item.prefix_mods:
                if p.stat_text not in [m.stat_text for m in test_item_with_mixed_tags.prefix_mods]:
                    added_mods.append((p.stat_text, p.tags))
            for s in result_item.suffix_mods:
                if s.stat_text not in [m.stat_text for m in test_item_with_mixed_tags.suffix_mods]:
                    added_mods.append((s.stat_text, s.tags))

    # Should have high success rate (collecting all tags prevents failures)
    assert successes >= 25, f"Success rate too low: {successes}/30. Should be ~30/30 with collective tag matching"

    # Check that added mods have matching tags
    visible_tags = {'attack', 'damage', 'caster', 'gem'}  # caster_damage is hidden

    for stat_text, tags in added_mods:
        mod_tags = set(tags) if tags else set()
        has_match = bool(visible_tags & mod_tags)
        assert has_match, f"Mod '{stat_text}' with tags {tags} doesn't match any visible tags: {visible_tags}"


def test_greater_homogenising_adds_two_mods(test_item_with_mixed_tags, modifier_pool):
    """Test that Greater Exaltation adds exactly 2 modifiers."""
    homogenising_omen = OmenInfo(
        id=1,
        name="Omen of Homogenising Exaltation",
        effect_description="Exalted adds matching tags",
        affected_currency="Exalted Orb",
        effect_type="homogenising",
        stack_size=10,
        rules=[]
    )

    greater_omen = OmenInfo(
        id=2,
        name="Omen of Greater Exaltation",
        effect_description="Exalted adds 2 mods",
        affected_currency="Exalted Orb",
        effect_type="greater",
        stack_size=10,
        rules=[]
    )

    config = {}
    base_exalted = ExaltedMechanic(config)
    exalted_with_homog = OmenModifiedMechanic(base_exalted, homogenising_omen)
    exalted_with_both = OmenModifiedMechanic(exalted_with_homog, greater_omen)

    test_item_copy = test_item_with_mixed_tags.model_copy(deep=True)
    success, message, result_item = exalted_with_both.apply(test_item_copy, modifier_pool)

    assert success, f"Greater + Homogenising failed: {message}"

    # Count total mods
    original_count = len(test_item_with_mixed_tags.prefix_mods) + len(test_item_with_mixed_tags.suffix_mods)
    result_count = len(result_item.prefix_mods) + len(result_item.suffix_mods)
    mods_added = result_count - original_count

    # Should add 2 mods (item has room: 2P + 1S = 3 total, can add 2 more suffixes)
    assert mods_added == 2, f"Expected 2 mods added, got {mods_added}"
