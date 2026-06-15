"""Tests for two alloy gaps fixed together:

1. Alloy-granted mods (Runic Alloys add a guaranteed Crafted mod, like essences) now appear in
   the Available Mods pool. They are crafted-only / weight-0 in pob-data, so - exactly like
   essence-only mods - they must be synthesized with explicit applicable_items to show up.
   Concretely: the Mystic Alloy "+Spirit" suffix must appear for boots.
2. The currency-tooltip endpoint now produces a real description + per-slot effects for alloys
   (previously it fell through every branch and returned description == name).
"""

from __future__ import annotations

import asyncio

import pytest

from app.api.v1.crafting import get_available_mods, get_currency_tooltip
from app.schemas.crafting import CraftableItem, ItemRarity
from app.schemas.item_bases import get_item_bases_by_slot


def _boots_item() -> CraftableItem:
    boots = get_item_bases_by_slot("boots")
    if not boots:
        pytest.skip("no boots bases loaded")
    b = boots[0]
    return CraftableItem(
        base_name=b.name, base_category=b.category, slot="boots",
        rarity=ItemRarity.RARE, item_level=83,
    )


# --- 1. alloy mods appear in the pool ------------------------------------------

def test_alloy_spirit_suffix_appears_on_boots():
    """The Mystic Alloy +Spirit suffix must be in the boots alloy_suffixes bucket."""
    res = asyncio.run(get_available_mods(_boots_item()))
    suffixes = res.get("alloy_suffixes", [])
    assert suffixes, "expected alloy suffixes for boots"
    spirit = [m for m in suffixes if "spirit" in m["stat_text"].lower()]
    assert spirit, f"no +Spirit alloy suffix on boots; got {[m['stat_text'] for m in suffixes]}"
    assert spirit[0]["mod_group"] == "BaseSpirit"


def test_alloy_mods_are_tagged_alloy_only():
    res = asyncio.run(get_available_mods(_boots_item()))
    for m in res.get("alloy_prefixes", []) + res.get("alloy_suffixes", []):
        assert "alloy_only" in m["tags"], f"alloy mod missing alloy_only tag: {m['stat_text']}"


def test_alloy_mods_excluded_from_regular_pool():
    """Alloy-only mods must not leak into the regular prefix/suffix lists."""
    res = asyncio.run(get_available_mods(_boots_item()))
    for m in res.get("prefixes", []) + res.get("suffixes", []):
        assert "alloy_only" not in m.get("tags", []), f"alloy mod leaked into regular pool: {m['stat_text']}"


def test_alloy_totals_match_lists():
    res = asyncio.run(get_available_mods(_boots_item()))
    assert res["total_alloy_prefixes"] == len(res["alloy_prefixes"])
    assert res["total_alloy_suffixes"] == len(res["alloy_suffixes"])


# --- 2. alloy tooltip has a real description -----------------------------------

def test_alloy_tooltip_has_description_and_effects():
    """A Runic Alloy tooltip must carry a real description and per-slot effects, not just its name."""
    t = asyncio.run(get_currency_tooltip("Mystic Alloy"))
    assert t["description"] and t["description"] != "Mystic Alloy", "alloy tooltip still shows only the name"
    assert "Crafted" in t["description"]
    assert t["type"] == "alloy"
    assert t["mechanics"], "alloy tooltip has no per-slot mechanics"
    assert "Spirit" in t["mechanics"], "Mystic Alloy mechanics should mention the boots Spirit effect"


def test_essence_tooltip_still_works():
    """Regression guard: the alloy branch must not break essence tooltips."""
    t = asyncio.run(get_currency_tooltip("Essence of the Body"))
    assert t["description"] and t["description"] != "Essence of the Body"
    assert t.get("mechanics")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
