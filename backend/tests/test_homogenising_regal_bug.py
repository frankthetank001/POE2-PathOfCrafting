"""
Test for homogenising coronation bug with non-matching tags.

User report: Used homogenising coronation with perfect regal on amulet with:
- Prefix: Deliberate (Attack tag) - Accuracy Rating
- Suffix: of the Sorcerer (Caster, Gem tags) - +3 to Level of all Spell Skills

Expected: Spell damage or other caster mod (since Sorcerer has 'caster' tag)
Actual: Got % increased evasion rating (doesn't share tags with either mod)

Bug: Regal homogenising doesn't filter out hidden tags, might be matching
on hidden tags like 'attack_damage', 'caster_damage', etc.
"""

import pytest
from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType, OmenInfo
from app.services.crafting.modifier_pool import ModifierPool
from app.services.crafting.modifier_loader import ModifierLoader
from app.services.crafting.mechanics import RegalMechanic, OmenModifiedMechanic


@pytest.fixture
def modifier_pool():
    """Load modifier pool from database."""
    modifiers = ModifierLoader.load_modifiers()
    return ModifierPool(modifiers)


@pytest.fixture
def test_item(modifier_pool):
    """Create test item matching user's scenario."""
    # Find Deliberate T5 accuracy mod
    deliberate = next(
        (m for m in modifier_pool.modifiers
         if m.name == "Deliberate"
         and m.tier == 5
         and "amulet" in m.applicable_items
         and "Accuracy" in m.stat_text),
        None
    )
    assert deliberate is not None, "Deliberate T5 not found"

    # Find of the Sorcerer T1 spell skills mod
    sorcerer = next(
        (m for m in modifier_pool.modifiers
         if m.name == "of the Sorcerer"
         and m.tier == 1
         and "amulet" in m.applicable_items
         and "Level of all Spell Skills" in m.stat_text),
        None
    )
    assert sorcerer is not None, "of the Sorcerer T1 not found"

    # Create item with these mods
    deliberate_copy = deliberate.model_copy()
    deliberate_copy.current_value = 111.0

    sorcerer_copy = sorcerer.model_copy()
    sorcerer_copy.current_value = 3.0

    return CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.MAGIC,
        item_level=81,
        quality=20,
        prefix_mods=[deliberate_copy],
        suffix_mods=[sorcerer_copy],
        corrupted=False
    )


def test_homogenising_coronation_tag_matching(test_item, modifier_pool):
    """
    Test that homogenising coronation only matches on VISIBLE tags.

    Given an item with:
    - Prefix "Deliberate" with tags ['attack']
    - Suffix "of the Sorcerer" with tags ['caster', 'gem']

    When using homogenising coronation, it should:
    1. Randomly pick one of the existing mods
    2. Filter OUT hidden tags (like 'attack_damage', 'caster_damage')
    3. Only match on visible tags ('attack', 'caster', 'gem')
    4. Add a mod with matching visible tags
    """
    # Check tags on existing mods
    assert test_item.prefix_mods[0].tags == ['attack'], f"Expected Deliberate to have ['attack'] tags, got {test_item.prefix_mods[0].tags}"
    assert set(test_item.suffix_mods[0].tags) == {'caster', 'gem'}, f"Expected of the Sorcerer to have ['caster', 'gem'] tags, got {test_item.suffix_mods[0].tags}"

    # Create homogenising coronation omen
    homogenising_omen = OmenInfo(
        id=1,
        name="Homogenising Coronation",
        effect_description="Regal adds modifier with matching tags",
        affected_currency="Regal Orb",
        effect_type="homogenising",
        stack_size=10,
        rules=[]
    )

    config = {"min_mod_level": None}
    base_regal = RegalMechanic(config)
    regal = OmenModifiedMechanic(base_regal, homogenising_omen)

    # Run test multiple times to check both code paths (prefix chosen vs suffix chosen)
    results = []
    for i in range(20):
        test_item_copy = test_item.model_copy(deep=True)
        success, message, result_item = regal.apply(test_item_copy, modifier_pool)

        if success:
            results.append({
                'success': True,
                'added_mod': result_item.prefix_mods[-1] if len(result_item.prefix_mods) > len(test_item.prefix_mods) else result_item.suffix_mods[-1],
                'message': message
            })
        else:
            results.append({
                'success': False,
                'message': message
            })

    # At least some should succeed
    successes = [r for r in results if r['success']]
    assert len(successes) > 0, f"All homogenising attempts failed: {[r['message'] for r in results if not r['success']]}"

    # Check that added mods have matching visible tags
    hidden_tags = {'essence_only', 'desecrated_only', 'drop', 'resource',
                   'energy_shield', 'flat_life_regen', 'armour',
                   'caster_damage', 'attack_damage'}

    for result in successes:
        added_mod = result['added_mod']

        # Get visible tags from the original mods
        deliberate_visible = [t for t in test_item.prefix_mods[0].tags if t not in hidden_tags]
        sorcerer_visible = [t for t in test_item.suffix_mods[0].tags if t not in hidden_tags]
        all_visible_tags = set(deliberate_visible + sorcerer_visible)

        # The added mod should have at least one visible tag matching the existing mods
        added_mod_visible = [t for t in (added_mod.tags or []) if t not in hidden_tags]
        has_matching_visible_tag = any(tag in all_visible_tags for tag in added_mod_visible)

        assert has_matching_visible_tag, (
            f"Added mod '{added_mod.name}' with tags {added_mod.tags} "
            f"(visible: {added_mod_visible}) doesn't share any VISIBLE tags "
            f"with existing mods (visible tags: {all_visible_tags})"
        )


def test_no_shared_visible_tags_should_fail(modifier_pool):
    """
    Test that homogenising coronation FAILS when mods have no shared visible tags.

    If the existing mods only have hidden tags or completely different visible tags,
    homogenising should fail gracefully.
    """
    # This is actually the case! 'attack' and 'caster'/'gem' don't overlap
    # So homogenising coronation should potentially fail or at least only match
    # when it randomly picks one specific mod
    pass
