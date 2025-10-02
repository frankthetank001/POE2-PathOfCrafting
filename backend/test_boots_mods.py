#!/usr/bin/env python3
"""Test script to verify boots get correct modifiers."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.crafting.modifier_loader import ModifierLoader
from app.services.crafting.modifier_pool import ModifierPool
from app.schemas.crafting import CraftableItem, ItemRarity

def test_boots_mods():
    """Test that boots get appropriate modifiers."""
    print("\nTesting Boots Modifier Pool")
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

    print(f"\nTest Item: {test_boots.base_name}")
    print(f"Category: {test_boots.base_category}")

    # Get all available mods
    prefixes = pool.get_all_mods_for_category(
        test_boots.base_category,
        "prefix",
        test_boots
    )

    suffixes = pool.get_all_mods_for_category(
        test_boots.base_category,
        "suffix",
        test_boots
    )

    print(f"\nTotal Prefixes: {len(prefixes)}")
    print(f"Total Suffixes: {len(suffixes)}")

    # Check for essence-only mods
    essence_prefixes = [m for m in prefixes if m.tags and "essence_only" in m.tags]
    essence_suffixes = [m for m in suffixes if m.tags and "essence_only" in m.tags]

    print(f"\nEssence-only Prefixes: {len(essence_prefixes)}")
    if essence_prefixes:
        for mod in essence_prefixes[:5]:
            print(f"  - {mod.name}: {mod.stat_text}")
    else:
        print("  [NONE FOUND - THIS IS THE BUG!]")

    print(f"\nEssence-only Suffixes: {len(essence_suffixes)}")
    if essence_suffixes:
        for mod in essence_suffixes[:5]:
            print(f"  - {mod.name}: {mod.stat_text}")
    else:
        print("  [NONE FOUND - THIS IS THE BUG!]")

    # Check for desecrated mods
    desecrated_prefixes = [m for m in prefixes if m.tags and "desecrated_only" in m.tags]
    desecrated_suffixes = [m for m in suffixes if m.tags and "desecrated_only" in m.tags]

    print(f"\nDesecrated-only Prefixes: {len(desecrated_prefixes)}")
    if desecrated_prefixes:
        for mod in desecrated_prefixes[:5]:
            print(f"  - {mod.name}: {mod.stat_text}")
    else:
        print("  [NONE FOUND - CHECKING WHY...]")

    print(f"\nDesecrated-only Suffixes: {len(desecrated_suffixes)}")
    if desecrated_suffixes:
        for mod in desecrated_suffixes[:5]:
            print(f"  - {mod.name}: {mod.stat_text}")
    else:
        print("  [NONE FOUND - CHECKING WHY...]")

    # Sample some regular prefixes
    print(f"\nSample Regular Prefixes:")
    regular_prefixes = [m for m in prefixes if not m.tags or ("essence_only" not in m.tags and "desecrated_only" not in m.tags)]
    for mod in regular_prefixes[:10]:
        print(f"  - {mod.name}: {mod.stat_text} - applicable_items: {mod.applicable_items}")

    # Check what essence mods exist in the full pool for boots
    print("\n" + "=" * 60)
    print("Checking ALL essence mods in database for boots...")
    print("=" * 60)

    all_essence_mods = [m for m in all_mods if m.tags and "essence_only" in m.tags]
    print(f"\nTotal essence-only mods in database: {len(all_essence_mods)}")

    boots_applicable = []
    for mod in all_essence_mods:
        if "boots" in mod.applicable_items or "armour" in mod.applicable_items:
            boots_applicable.append(mod)

    print(f"Essence mods applicable to boots: {len(boots_applicable)}")
    if boots_applicable:
        print("\nSample essence mods that should appear:")
        for mod in boots_applicable[:10]:
            print(f"  - {mod.name} ({mod.mod_type}): {mod.stat_text}")
            print(f"    applicable_items: {mod.applicable_items}")
            print(f"    tags: {mod.tags}")

if __name__ == "__main__":
    test_boots_mods()
