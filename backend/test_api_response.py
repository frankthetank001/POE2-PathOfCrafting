#!/usr/bin/env python3
"""Test API response format for hybrid modifiers."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.crafting.modifier_loader import ModifierLoader
from app.services.crafting.modifier_pool import ModifierPool
from app.schemas.crafting import CraftableItem, ItemRarity
import json

def test_api_json_response():
    """Test that API JSON response includes current_values for hybrid mods."""
    print("\nTesting API JSON Response Format")
    print("=" * 60)

    # Load modifiers
    all_mods = ModifierLoader.get_modifiers()
    pool = ModifierPool(all_mods)

    # Create test item
    test_item = CraftableItem(
        base_name="Vile Robe",
        base_category="int_armour",
        rarity=ItemRarity.RARE,
        item_level=82,
        quality=20
    )

    # Add a random modifier
    print("Rolling a random modifier...")
    rolled_mod = pool.roll_random_modifier(
        mod_type="prefix",
        item_category="int_armour",
        item_level=82,
        item=test_item
    )

    if rolled_mod:
        # Convert to dict (simulating API response)
        mod_dict = rolled_mod.model_dump()

        print(f"\nModifier: {rolled_mod.name}")
        print(f"Stat Text: {rolled_mod.stat_text}")
        print(f"\nJSON Response:")
        print(json.dumps(mod_dict, indent=2))

        if rolled_mod.stat_ranges and len(rolled_mod.stat_ranges) > 1:
            print(f"\n[HYBRID MOD DETECTED]")
            print(f"✓ stat_ranges: {mod_dict.get('stat_ranges')}")
            print(f"✓ current_values: {mod_dict.get('current_values')}")

            if mod_dict.get('current_values') and len(mod_dict['current_values']) > 1:
                print(f"\n[OK] API will send multiple values to frontend!")
            else:
                print(f"\n[ERROR] API is not sending multiple values!")

if __name__ == "__main__":
    test_api_json_response()
