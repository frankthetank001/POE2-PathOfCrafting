"""Regression tests for essence/alloy applicability on weapons.

Bug: essences were wrongly greyed out on quarterstaves (and axes/maces/swords). The essence
data uses granular item_types ("One Hand Sword", "Warstaff", "Buckler"), but
ESSENCE_ITEM_TYPE_TO_CATEGORY only had grouped/aliased keys ("One Handed Melee Weapon",
"Quarterstaff"), so the multi-word types resolved to nothing and can_apply returned False.

These tests pin: (1) Perfect Essence of Battle applies to the weapon classes it targets,
incl. the quarterstaff from the user report, and (2) EVERY item_type used by the essence/alloy
data resolves to at least one real base (guards the whole class of mapping gaps).
"""

from __future__ import annotations

import pytest

from app.core.item_classification import ESSENCE_ITEM_TYPE_TO_CATEGORY
from app.schemas.crafting import CraftableItem, ItemModifier, ItemRarity, ModType
from app.schemas.item_bases import ITEM_BASES, get_item_base_by_name
from app.services.crafting.config_service import crafting_config_service
from app.services.crafting.unified_factory import unified_crafting_factory


def _rare(base_name: str) -> CraftableItem:
    b = get_item_base_by_name(base_name)
    assert b is not None, f"base {base_name} not found"
    return CraftableItem(
        base_name=b.name, base_category=b.category, slot=b.slot,
        rarity=ItemRarity.RARE, item_level=80,
        prefix_mods=[ItemModifier(name="p", mod_type=ModType.PREFIX, tier=1,
                                  stat_text="Adds # to # Fire Damage", current_value=1)],
    )


def _battle():
    ess = unified_crafting_factory.create_currency("Perfect Essence of Battle")
    if ess is None:
        pytest.skip("Perfect Essence of Battle not available")
    return ess


def _one_base_per_category(*slots):
    seen = {}
    for b in ITEM_BASES:
        if b.slot in slots and b.category not in seen:
            seen[b.category] = b.name
    return seen


def test_battle_applies_to_quarterstaff():
    """The exact user report: a rare Quarterstaff must NOT be greyed for Essence of Battle."""
    qs = next((b for b in ITEM_BASES if "Quarterstaff" in b.name), None)
    if qs is None:
        pytest.skip("no quarterstaff base")
    ok, reason = _battle().can_apply(_rare(qs.name), for_display=True)
    assert ok is True, f"quarterstaff wrongly greyed: {reason}"


def test_battle_applies_to_its_melee_targets():
    """Battle targets axes/maces/swords (via One/Two Hand X) - none should be greyed."""
    ess = _battle()
    by_cat = _one_base_per_category("weapons - 1 hand", "weapons - 2 hand")
    for cat in ("axe", "mace", "sword", "spear", "flail"):
        if cat not in by_cat:
            continue
        ok, reason = ess.can_apply(_rare(by_cat[cat]), for_display=True)
        assert ok is True, f"Battle wrongly greyed on {cat}: {reason}"


def test_battle_still_greyed_on_untargeted_weapons():
    """The fix must not over-apply: Battle doesn't target claws/foci, so they stay greyed."""
    ess = _battle()
    by_cat = _one_base_per_category("weapons - 1 hand", "weapons - 2 hand", "offhand")
    for cat in ("claw", "focus"):
        if cat not in by_cat:
            continue
        ok, _ = ess.can_apply(_rare(by_cat[cat]), for_display=True)
        assert ok is False, f"Battle should not apply to {cat}"


def test_every_essence_item_type_resolves_to_a_base():
    """Systemic guard: every item_type the essence data uses must resolve to a real base
    (via the mapping or the lowercase fallback), or its essences are always greyed."""
    crafting_config_service.ensure_loaded()
    base_cats = {b.category for b in ITEM_BASES}

    def resolves(item_type: str) -> bool:
        mapped = ESSENCE_ITEM_TYPE_TO_CATEGORY.get(item_type, [])
        if set(mapped) & base_cats:
            return True
        # mirror the lowercase fallback in EssenceMechanic._effect_applies_to_item
        return item_type.lower().replace(" ", "_") in base_cats

    item_types = {
        eff.item_type
        for cfg in crafting_config_service._essence_configs.values()
        for eff in cfg.item_effects
    }
    unresolved = sorted(it for it in item_types if not resolves(it))
    assert not unresolved, f"essence item_types that resolve to no base: {unresolved}"


def test_every_alloy_item_type_resolves_to_a_base():
    """Same guard for alloy effects."""
    crafting_config_service.ensure_loaded()
    base_cats = {b.category for b in ITEM_BASES}

    def resolves(item_type: str) -> bool:
        mapped = ESSENCE_ITEM_TYPE_TO_CATEGORY.get(item_type, [])
        if set(mapped) & base_cats:
            return True
        return item_type.lower().replace(" ", "_") in base_cats

    item_types = {
        eff.item_type
        for cfg in crafting_config_service._alloy_configs.values()
        for eff in cfg.item_effects
    }
    unresolved = sorted(it for it in item_types if not resolves(it))
    assert not unresolved, f"alloy item_types that resolve to no base: {unresolved}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
