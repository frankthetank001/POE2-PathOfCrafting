"""
Test that Homogenising Coronation respects exclusion groups.

When an item has "+3 to Level of all Spell Skills", homogenising should NOT
be able to add "+to Level of all Minion Skills" because they're in the same
exclusion group.
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
def test_item_with_spell_skills(modifier_pool):
    """Create item with +3 to Level of all Spell Skills."""
    spell_skills_mod = next(
        (m for m in modifier_pool.modifiers
         if "Level of all Spell Skills" in m.stat_text
         and m.mod_type == ModType.SUFFIX
         and "amulet" in m.applicable_items),
        None
    )
    assert spell_skills_mod is not None, "+Level of all Spell Skills not found"

    deliberate = next(
        (m for m in modifier_pool.modifiers
         if m.name == "Deliberate"
         and m.tier == 5
         and "amulet" in m.applicable_items
         and "Accuracy" in m.stat_text),
        None
    )
    assert deliberate is not None, "Deliberate not found"

    spell_copy = spell_skills_mod.model_copy()
    spell_copy.current_value = 3.0

    deliberate_copy = deliberate.model_copy()
    deliberate_copy.current_value = 111.0

    return CraftableItem(
        base_name="Gold Amulet",
        base_category="amulet",
        rarity=ItemRarity.MAGIC,
        item_level=81,
        quality=20,
        prefix_mods=[deliberate_copy],
        suffix_mods=[spell_copy],
        corrupted=False
    )


def test_homogenising_respects_exclusion_groups(test_item_with_spell_skills, modifier_pool):
    """
    Test that Homogenising Coronation does NOT add mods from same exclusion group.
    
    Item has: +3 to Level of all Spell Skills
    Should NOT add: +Level of all Minion Skills (same exclusion group)
    Should NOT add: +Level of all Melee Skills (same exclusion group)
    """
    # Create homogenising omen
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

    # Run 50 tests
    added_mods = []
    for i in range(50):
        test_item_copy = test_item_with_spell_skills.model_copy(deep=True)
        success, message, result_item = regal.apply(test_item_copy, modifier_pool)

        if success:
            # Find added mod
            if len(result_item.suffix_mods) > len(test_item_with_spell_skills.suffix_mods):
                added_mod = result_item.suffix_mods[-1]
                added_mods.append(added_mod.stat_text)

    # Check that none of the added mods are in the same exclusion group
    forbidden_mods = [
        "Level of all Minion Skills",
        "Level of all Melee Skills",
        "Level of all Projectile Skills",
        "Level of all Attack Skills",
        "Level of all Skills",
        "Level of all Cold Spell Skills",
        "Level of all Fire Spell Skills",
        "Level of all Lightning Spell Skills",
        "Level of all Physical Spell Skills",
        "Level of all Chaos Spell Skills",
    ]

    violations = [mod for mod in added_mods if any(forbidden in mod for forbidden in forbidden_mods)]

    assert len(violations) == 0, (
        f"Homogenising added mods from same exclusion group as Spell Skills:\n"
        f"Violations: {violations}\n"
        f"All added mods: {set(added_mods)}"
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
