"""Tests for the Runic Alloy crafting mechanic (PoE2 0.5).

An alloy removes a random modifier from a Rare item and adds the alloy's guaranteed CRAFTED
modifier for that item's slot (structurally a Perfect Essence, but the added mod is the single
teal crafted mod, max 1 per item). Effects come from source_data/alloys.json.
"""

import pytest

from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType
from app.services.crafting.config_service import crafting_config_service
from app.services.crafting.unified_factory import unified_crafting_factory
from app.services.crafting.simulator import CraftingSimulator


@pytest.fixture(scope="module")
def simulator():
    return CraftingSimulator()


def _rare_boots():
    return CraftableItem(
        base_name="Lattice Sandals", base_category="dex_armour", slot="boots",
        rarity=ItemRarity.RARE, item_level=82,
        prefix_mods=[ItemModifier(name="Life", mod_type=ModType.PREFIX, tier=1,
                                  stat_text="+# to maximum Life", current_value=100,
                                  mod_group="IncreasedLife")],
        suffix_mods=[ItemModifier(name="ColdRes", mod_type=ModType.SUFFIX, tier=1,
                                  stat_text="+#% to Cold Resistance", current_value=40,
                                  mod_group="ColdResistance")],
    )


def test_alloy_configs_loaded():
    crafting_config_service.ensure_loaded()
    names = crafting_config_service.get_all_alloy_names()
    assert len(names) == 13, names
    assert "Mystic Alloy" in names
    # Every alloy is registered as an applyable currency.
    for name in names:
        assert unified_crafting_factory.create_currency(name) is not None


def test_mystic_alloy_adds_crafted_spirit_on_boots(simulator):
    boots = _rare_boots()
    alloy = unified_crafting_factory.create_currency("Mystic Alloy")
    assert type(alloy).__name__ == "AlloyMechanic"
    ok, err = alloy.can_apply(boots)
    assert ok, err
    success, msg, result = alloy.apply(boots, simulator.modifier_pool)
    assert success, msg
    crafted = [m for m in result.prefix_mods + result.suffix_mods if m.is_crafted]
    assert len(crafted) == 1
    mod = crafted[0]
    assert "Spirit" in mod.stat_text
    assert mod.mod_type == ModType.SUFFIX
    # It rolled within the alloy's range and is flagged, not essence-only.
    assert 10 <= (mod.current_value or 0) <= 15
    assert mod.is_essence_only is False
    assert "alloy_guaranteed" in (mod.tags or [])


def test_only_one_crafted_mod_allowed(simulator):
    boots = _rare_boots()
    _, _, result = unified_crafting_factory.create_currency("Mystic Alloy").apply(boots, simulator.modifier_pool)
    # A second alloy must be rejected - an item can hold only one crafted mod.
    ok, err = unified_crafting_factory.create_currency("Cyclonic Alloy").can_apply(result)
    assert not ok
    assert "crafted" in err.lower()


def test_alloy_slot_applicability():
    ring = CraftableItem(base_name="Iron Ring", base_category="ring", slot="ring",
                         rarity=ItemRarity.RARE, item_level=82,
                         prefix_mods=[ItemModifier(name="x", mod_type=ModType.PREFIX, tier=1,
                                                   stat_text="+# to maximum Life", current_value=10,
                                                   mod_group="IncreasedLife")])
    # Mystic Alloy has no ring effect -> rejected; Runic Alloy has a ring effect -> accepted.
    ok_mystic, _ = unified_crafting_factory.create_currency("Mystic Alloy").can_apply(ring)
    ok_runic, _ = unified_crafting_factory.create_currency("Runic Alloy").can_apply(ring)
    assert not ok_mystic
    assert ok_runic


def test_alloys_only_apply_to_rare(simulator):
    magic_boots = CraftableItem(base_name="Lattice Sandals", base_category="dex_armour", slot="boots",
                                rarity=ItemRarity.MAGIC, item_level=82)
    ok, err = unified_crafting_factory.create_currency("Mystic Alloy").can_apply(magic_boots)
    assert not ok
    assert "Rare" in err


def test_alloys_offered_in_available_currencies(simulator):
    boots = _rare_boots()
    available = simulator.get_available_currencies(boots)
    offered = [c for c in available if "Alloy" in c]
    # Boots should be offered the alloys that define a boots/armour effect.
    assert "Mystic Alloy" in offered
    assert "Cyclonic Alloy" in offered


def test_every_alloy_effect_resolves_to_a_real_mod():
    """Each alloy's per-slot mod_id must exist in the pob-data mod pool."""
    from app.services.crafting.pob_data_loader import get_pob_data_loader
    loader = get_pob_data_loader()
    crafting_config_service.ensure_loaded()
    for name in crafting_config_service.get_all_alloy_names():
        cfg = crafting_config_service.get_alloy_config(name)
        assert cfg.item_effects, f"{name} has no effects"
        for eff in cfg.item_effects:
            assert eff.mod_id, f"{name}/{eff.item_type} missing mod_id"
            assert loader.get_modifier_by_id(eff.mod_id) is not None, (
                f"{name}/{eff.item_type}: mod_id {eff.mod_id} not in pool"
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
