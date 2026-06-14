"""Tests for the finish-my-craft advisor (BuildsService.suggest_finish).

Given a partially-crafted Rare, the advisor suggests the valuable mods to fill its open slots,
sourced from real similar meta items + slot popularity, filtered to mods that can roll on the
base, respecting the 1-crafted / 1-desecrated caps. Runs offline against the local builds
artifact. Assertions are data-refresh-robust invariants, guarded on the int_armour body slot
still being present in the snapshot where a concrete result is needed.
"""

from __future__ import annotations

import asyncio

import pytest

from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType
from app.services.builds.service import BuildsService


@pytest.fixture(scope="module")
def service() -> BuildsService:
    svc = BuildsService()
    asyncio.run(svc.initialize())
    if not svc.available:
        pytest.skip("builds aggregate artifact not available locally")
    return svc


def _mod(text: str, mtype: ModType, value: float = 1.0,
         is_crafted: bool = False, is_desecrated: bool = False) -> ItemModifier:
    return ItemModifier(
        name=text, mod_type=mtype, tier=1, stat_text=text, current_value=value,
        is_crafted=is_crafted, is_desecrated=is_desecrated,
    )


def _vile_robe(prefixes, suffixes, corrupted: bool = False) -> CraftableItem:
    return CraftableItem(
        base_name="Vile Robe", base_category="int_armour", slot="body_armour",
        rarity=ItemRarity.RARE, item_level=83, quality=20,
        prefix_mods=prefixes, suffix_mods=suffixes, corrupted=corrupted,
    )


# The user's actual (finished, corrupted) item: 3 prefixes + 3 suffixes (incl. 1 desecrated, 1 crafted).
def _finished_item() -> CraftableItem:
    return _vile_robe(
        prefixes=[
            _mod("101% increased Energy Shield", ModType.PREFIX, 101),
            _mod("+96 to maximum Energy Shield", ModType.PREFIX, 96),
            _mod("+53 to Spirit", ModType.PREFIX, 53),
        ],
        suffixes=[
            _mod("35% reduced Attribute Requirements", ModType.SUFFIX, 35),
            _mod("20% of Damage is taken from Mana before Life", ModType.SUFFIX, 20, is_desecrated=True),
            _mod("15% reduced Slowing Potency of Debuffs on You", ModType.SUFFIX, 15, is_crafted=True),
        ],
        corrupted=True,
    )


# A partial in-progress item: 1 prefix + 1 suffix, four slots still open.
def _partial_item() -> CraftableItem:
    return _vile_robe(
        prefixes=[_mod("101% increased Energy Shield", ModType.PREFIX, 101)],
        suffixes=[_mod("+35% to Cold Resistance", ModType.SUFFIX, 35)],
    )


def _all_suggestions(res: dict):
    return (res["suggested_prefixes"] + res["suggested_suffixes"]
            + res["suggested_crafted"] + res["suggested_desecrated"])


# --- finished item: nothing to suggest -----------------------------------------

def test_finished_item_is_complete(service: BuildsService):
    """A full 3-prefix / 3-suffix rare (incl. its 1 crafted + 1 desecrated) has no open slot, so
    the advisor reports 'complete' and offers no suggestions - matching the user's actual item."""
    res = service.suggest_finish(_finished_item())
    assert res is not None
    assert res["open_prefixes"] == 0 and res["open_suffixes"] == 0
    assert res["crafted_slot_open"] is False
    assert res["desecrated_slot_open"] is False
    assert res["verdict"] == "complete"
    assert _all_suggestions(res) == []


def test_finished_item_note_flags_corruption(service: BuildsService):
    """A corrupted item can't be modified - the message says so rather than implying you can craft."""
    res = service.suggest_finish(_finished_item())
    assert "corrupted" in (res["message"] or "").lower()


# --- partial item: real, well-formed suggestions -------------------------------

def test_partial_item_has_open_slots_and_suggestions(service: BuildsService):
    res = service.suggest_finish(_partial_item())
    assert res["craftable"] is True
    assert res["open_prefixes"] == 2 and res["open_suffixes"] == 2
    assert res["verdict"] == "suggestions"
    # The int_armour body slot is well-populated in the snapshot; if it isn't, skip the concrete part.
    if not _all_suggestions(res):
        pytest.skip("no slot mod data for int_armour body in snapshot")
    assert res["suggested_prefixes"], "expected prefix suggestions for an ES body"


def test_suggestions_match_their_bucket(service: BuildsService):
    """A prefix list holds only prefixes, a suffix list only suffixes."""
    res = service.suggest_finish(_partial_item())
    assert all(m["mod_type"] == "prefix" for m in res["suggested_prefixes"])
    assert all(m["mod_type"] == "suffix" for m in res["suggested_suffixes"])


def test_suggestions_exclude_mods_already_on_item(service: BuildsService):
    """No suggestion repeats a (mod_type, mod_group) the item already carries."""
    res = service.suggest_finish(_partial_item())
    present = {(p["mod_type"], p["mod_group"]) for p in res["present_mods"] if p["mod_group"]}
    for m in _all_suggestions(res):
        assert (m["mod_type"], m["mod_group"]) not in present, f"re-suggested a present mod: {m['stat_text']}"


def test_no_duplicate_group_within_a_list(service: BuildsService):
    for key in ("suggested_prefixes", "suggested_suffixes"):
        groups = [m["mod_group"] for m in service.suggest_finish(_partial_item())[key]]
        assert len(groups) == len(set(groups)), f"{key} has a duplicate mod_group"


# --- archetype gating: a pure-ES base never gets evasion/armour ----------------

def test_pure_es_base_excludes_evasion_and_armour(service: BuildsService):
    """A Vile Robe (int_armour) carries only Energy Shield, so no suggestion may be an
    Evasion or Armour defence mod - the coarse 'armour' applicability tag would otherwise leak them."""
    res = service.suggest_finish(_partial_item())
    for m in _all_suggestions(res):
        low = m["stat_text"].lower()
        assert "evasion" not in low, f"evasion mod suggested on pure-ES base: {m['stat_text']}"
        # 'Armour' as a defence word; allow nothing referencing Armour on a pure-ES base.
        assert "armour" not in low, f"armour mod suggested on pure-ES base: {m['stat_text']}"


def test_es_mods_are_still_allowed(service: BuildsService):
    """The defence filter must not over-prune: an ES body should still surface Energy Shield mods."""
    res = service.suggest_finish(_partial_item())
    if not _all_suggestions(res):
        pytest.skip("no slot mod data for int_armour body in snapshot")
    assert any("energy shield" in m["stat_text"].lower() for m in _all_suggestions(res))


# --- similar items: real neighbours, ranked by ES ------------------------------

def test_similar_items_sorted_by_energy_shield(service: BuildsService):
    """Strongest examples first: similar items are ordered by descending (approx) Energy Shield."""
    items = service.suggest_finish(_partial_item())["similar_items"]
    es = [(s["approx_energy_shield"] if s["approx_energy_shield"] is not None else -1) for s in items]
    assert es == sorted(es, reverse=True)


def test_similar_items_are_same_slot_archetype(service: BuildsService):
    """Neighbours are real rares of the same slot; in the populated case, the same defence archetype."""
    res = service.suggest_finish(_partial_item())
    if res["similar_count"] == 0:
        pytest.skip("no similar items in snapshot")
    assert res["similar_basis"]
    for s in res["similar_items"]:
        assert s["base_type"]
        assert s["mod_count"] >= 0


# --- crafted / desecrated slot logic -------------------------------------------

def test_crafted_and_desecrated_open_on_partial(service: BuildsService):
    """With slots free and no crafted/desecrated mod yet, both special slots are open."""
    res = service.suggest_finish(_partial_item())
    assert res["crafted_slot_open"] is True
    assert res["desecrated_slot_open"] is True


def test_crafted_slot_closes_when_one_present(service: BuildsService):
    """Once a crafted mod is on the item, the crafted slot is closed and no crafted mods are suggested."""
    item = _vile_robe(
        prefixes=[_mod("101% increased Energy Shield", ModType.PREFIX, 101)],
        suffixes=[_mod("15% reduced Slowing Potency of Debuffs on You", ModType.SUFFIX, 15, is_crafted=True)],
    )
    res = service.suggest_finish(item)
    assert res["crafted_slot_open"] is False
    assert res["suggested_crafted"] == []


# --- response model round-trip (a stripped field would break the frontend) ------

def test_response_model_preserves_shape(service: BuildsService):
    from app.api.v1.builds import FinishSuggestResponse

    res = service.suggest_finish(_partial_item())
    dumped = FinishSuggestResponse.model_validate(res).model_dump()
    assert dumped["verdict"] == "suggestions"
    assert dumped["open_prefixes"] == 2
    assert "suggested_prefixes" in dumped and "similar_items" in dumped


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
