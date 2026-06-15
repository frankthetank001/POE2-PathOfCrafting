"""Regression tests for separating quarterstaff (warstaff, martial) from caster staff.

Bug: quarterstaves and caster staves both loaded as base category "staff", so a quarterstaff
wrongly showed caster spell mods (and caster essences) and was missing its martial mods. The
two pob-data weapon classes are distinguished by tag ("warstaff" vs "staff"); the loader now
categorises quarterstaves as "warstaff".

These pin: the categories are distinct, the quarterstaff pool is martial (no spell mods), the
caster-staff pool is caster (spell mods), and essence applicability follows the split.
"""

from __future__ import annotations

import asyncio

import pytest

from app.api.v1.crafting import get_available_mods
from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType
from app.schemas.item_bases import ITEM_BASES, get_item_base_by_name
from app.services.crafting.unified_factory import unified_crafting_factory


def _quarterstaff_base():
    return next((b for b in ITEM_BASES if "Quarterstaff" in b.name), None)


def _caster_staff_base():
    return next((b for b in ITEM_BASES if b.name.endswith(" Staff") and "Quarter" not in b.name), None)


def _pool(base) -> list:
    item = CraftableItem(base_name=base.name, base_category=base.category, slot=base.slot,
                         rarity=ItemRarity.RARE, item_level=82)
    res = asyncio.run(get_available_mods(item))
    return res["prefixes"] + res["suffixes"]


def test_quarterstaff_and_caster_staff_have_distinct_categories():
    qs, st = _quarterstaff_base(), _caster_staff_base()
    if not qs or not st:
        pytest.skip("staff/quarterstaff bases not present")
    assert qs.category == "warstaff", f"quarterstaff should be 'warstaff', got {qs.category}"
    assert st.category == "staff", f"caster staff should be 'staff', got {st.category}"


def test_quarterstaff_pool_is_martial_no_spell():
    qs = _quarterstaff_base()
    if not qs:
        pytest.skip("no quarterstaff base")
    mods = _pool(qs)
    spell = [m for m in mods if "spell" in m["stat_text"].lower()]
    assert not spell, f"quarterstaff should have no spell mods, found {len(spell)}: {[m['stat_text'] for m in spell[:3]]}"
    # And it should have its martial mods (added damage / attack speed).
    martial = [m for m in mods if "adds" in m["stat_text"].lower() and "damage" in m["stat_text"].lower()]
    assert martial, "quarterstaff should have martial added-damage mods"


def test_caster_staff_pool_has_spell_mods():
    st = _caster_staff_base()
    if not st:
        pytest.skip("no caster staff base")
    mods = _pool(st)
    spell = [m for m in mods if "spell" in m["stat_text"].lower()]
    assert spell, "caster staff should have spell mods"


def test_martial_essence_applies_to_quarterstaff_not_caster_staff():
    qs, st = _quarterstaff_base(), _caster_staff_base()
    if not qs or not st:
        pytest.skip("bases missing")
    battle = unified_crafting_factory.create_currency("Perfect Essence of Battle")
    if battle is None:
        pytest.skip("essence unavailable")

    def mk(b):
        # remove_add_rare essences need >=1 existing mod (they remove one), like the user's item.
        return CraftableItem(
            base_name=b.name, base_category=b.category, slot=b.slot,
            rarity=ItemRarity.RARE, item_level=82,
            prefix_mods=[ItemModifier(name="x", mod_type=ModType.PREFIX, tier=1,
                                      stat_text="Adds # to # Fire Damage", current_value=1)],
        )

    assert battle.can_apply(mk(qs), for_display=True)[0] is True, "Battle should apply to quarterstaff"
    assert battle.can_apply(mk(st), for_display=True)[0] is False, "Battle should NOT apply to caster staff"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
