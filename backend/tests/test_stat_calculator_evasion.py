"""Regression tests for defence stat calculation - specifically Evasion not updating.

Two bugs were fixed:
1. _calculate_percentage_bonuses tested single-stat phrases before hybrids, so "increased
   Evasion and Energy Shield" matched "increased Evasion"/"...Armour" first and the second
   defence was dropped (evasion never moved on hybrid mods).
2. Matching required the '#'-template stat_text; the frontend's manual drag-add substitutes
   rolled numbers in ("50% increased Evasion Rating"), which never matched -> bonus dropped.

These pin both forms (template + numeric) and pure/hybrid/triple defence mods, plus the
/calculate-stats endpoint round-trip.
"""

from __future__ import annotations

import asyncio

import pytest

from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType
from app.schemas.item_bases import get_item_bases_by_slot
from app.services.stat_calculator import StatCalculator


def _ev_only_body():
    for b in get_item_bases_by_slot("body_armour"):
        bs = b.base_stats or {}
        if "Evasion" in bs and "Armour" not in bs:
            return b
    return None


def _ar_ev_body():
    for b in get_item_bases_by_slot("body_armour"):
        bs = b.base_stats or {}
        if "Evasion" in bs and "Armour" in bs:
            return b
    return None


def _item(base, stat_text, value):
    return CraftableItem(
        base_name=base.name, base_category=base.category, slot=base.slot,
        rarity=ItemRarity.RARE, item_level=82, quality=0,
        prefix_mods=[ItemModifier(name="m", mod_type=ModType.PREFIX, tier=1,
                                  stat_text=stat_text, current_value=value)],
    )


def _ev(base, stat_text, value):
    return StatCalculator.calculate_stats(_item(base, stat_text, value)).get("Evasion")


def test_pure_evasion_template_and_numeric_both_apply():
    b = _ev_only_body()
    if not b:
        pytest.skip("no evasion-only body base")
    base_ev = b.base_stats["Evasion"]
    # '#'-template form (backend pool mods) and numeric form (frontend drag-add) must both work.
    assert _ev(b, "#% increased Evasion Rating", 50) == int(base_ev * 1.5)
    assert _ev(b, "50% increased Evasion Rating", 50) == int(base_ev * 1.5)
    assert _ev(b, "+150 to Evasion Rating", 150) == base_ev + 150


def test_hybrid_evasion_energy_shield_updates_evasion():
    """The reported bug: a hybrid 'increased Evasion and Energy Shield' must move Evasion."""
    b = _ev_only_body()
    if not b:
        pytest.skip("no evasion-only body base")
    base_ev = b.base_stats["Evasion"]
    assert _ev(b, "50% increased Evasion and Energy Shield", 50) == int(base_ev * 1.5)


def test_hybrid_armour_evasion_updates_both():
    b = _ar_ev_body()
    if not b:
        pytest.skip("no armour/evasion body base")
    stats = StatCalculator.calculate_stats(_item(b, "50% increased Armour and Evasion", 50))
    assert stats["Armour"] == int(b.base_stats["Armour"] * 1.5)
    assert stats["Evasion"] == int(b.base_stats["Evasion"] * 1.5)


def test_triple_armour_evasion_es_updates_all():
    b = _ar_ev_body()
    if not b:
        pytest.skip("no armour/evasion body base")
    stats = StatCalculator.calculate_stats(_item(b, "30% increased Armour, Evasion and Energy Shield", 30))
    assert stats["Armour"] == int(b.base_stats["Armour"] * 1.3)
    assert stats["Evasion"] == int(b.base_stats["Evasion"] * 1.3)


def test_calculate_stats_endpoint_round_trip():
    """The frontend's recompute path: POST /calculate-stats returns updated calculated_stats."""
    from app.api.v1.crafting import calculate_stats

    b = _ev_only_body()
    if not b:
        pytest.skip("no evasion-only body base")
    item = _item(b, "50% increased Evasion Rating", 50)
    result = asyncio.run(calculate_stats(item))
    assert result.calculated_stats.get("Evasion") == int(b.base_stats["Evasion"] * 1.5)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
