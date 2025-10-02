#!/usr/bin/env python3
"""Test that body_armour mods don't appear on boots."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.crafting.modifier_loader import ModifierLoader
from app.services.crafting.modifier_pool import ModifierPool
from app.schemas.crafting import CraftableItem, ItemRarity

def test_body_armour_exclusion():
    """Test that body_armour-only mods don't appear on boots."""
    print("\nTesting Body Armour Mod Exclusion from Boots")
    print("=" * 60)

    # Load modifiers
    all_mods = ModifierLoader.get_modifiers()
    pool = ModifierPool(all_mods)

    # Create test boots item
    test_boots = CraftableItem(
        base_name="Iron Greaves",
        base_category="str_armour",
        rarity=ItemRarity.NORMAL,
        item_level=82,
        quality=0
    )

    # Get all available mods for boots
    prefixes = pool.get_all_mods_for_category(
        test_boots.base_category,
        "prefix",
        test_boots
    )

    # Check for body_armour-only mods (these should NOT appear)
    body_armour_only_mods = []
    for mod in prefixes:
        if "body_armour" in mod.applicable_items and "boots" not in mod.applicable_items:
            body_armour_only_mods.append(mod)

    print(f"\nBody armour-only mods found in boots pool: {len(body_armour_only_mods)}")
    if body_armour_only_mods:
        print("\n[ERROR] These body_armour mods should NOT appear on boots:")
        for mod in body_armour_only_mods[:10]:
            print(f"  - {mod.name}: {mod.stat_text}")
            print(f"    applicable_items: {mod.applicable_items}")
    else:
        print("[OK] No body_armour-only mods in boots pool!")

    # Now test body armour to ensure it still gets body_armour mods
    print("\n" + "=" * 60)
    print("Testing Body Armour Still Gets Body Armour Mods")
    print("=" * 60)

    test_body_armour = CraftableItem(
        base_name="Vile Robe",
        base_category="int_armour",
        rarity=ItemRarity.NORMAL,
        item_level=82,
        quality=20
    )

    body_prefixes = pool.get_all_mods_for_category(
        test_body_armour.base_category,
        "prefix",
        test_body_armour
    )

    body_armour_mods = []
    for mod in body_prefixes:
        if "body_armour" in mod.applicable_items:
            body_armour_mods.append(mod)

    print(f"\nBody armour mods in body armour pool: {len(body_armour_mods)}")
    if body_armour_mods:
        print("\n[OK] Body armour still gets body_armour mods:")
        for mod in body_armour_mods[:5]:
            print(f"  - {mod.name}: {mod.stat_text}")
    else:
        print("\n[ERROR] Body armour lost its body_armour mods!")

if __name__ == "__main__":
    test_body_armour_exclusion()
