"""Test to understand why Vile Robe (int_armour body_armour) gets % increased Armour mods"""
import json

# Load modifiers
with open('backend/source_data/modifiers.json') as f:
    mods = json.load(f)

# Find "Impenetrable" - the mod showing up on Vile Robe
impenetrable = [m for m in mods if m.get('name') == 'Impenetrable'][0]

print(f"Mod: {impenetrable['name']}")
print(f"Stat text: {impenetrable['stat_text']}")
print(f"Applicable items: {impenetrable['applicable_items']}")
print(f"Tier: {impenetrable['tier']}")

# Simulate the filtering logic for a Vile Robe (int_armour, body_armour slot)
item_category = "int_armour"
item_slot = "body_armour"  # This is the key - it's a body armour piece
mod_applicable_items = impenetrable['applicable_items']

print(f"\n--- Simulating _is_mod_applicable_to_category logic ---")
print(f"item_category: {item_category}")
print(f"item_slot: {item_slot}")
print(f"mod.applicable_items: {mod_applicable_items}")

# Line 373-374: Direct category match
if item_category in mod_applicable_items:
    print("\nLine 373-374: item_category in mod.applicable_items -> RETURN TRUE")
else:
    print("\nLine 373-374: No direct category match")

# Line 377-378: Slot match
if item_slot and item_slot in mod_applicable_items:
    print(f"Line 377-378: item_slot '{item_slot}' in mod.applicable_items -> RETURN TRUE")
else:
    print(f"Line 377-378: item_slot NOT in mod.applicable_items")

# Line 381-384: Check armour categories
if item_category in ["int_armour", "str_armour", "dex_armour", "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour"]:
    print("\nLine 381: Item category is an armour type")

    # Line 383: Check for "armour" universal category
    if "armour" in mod_applicable_items:
        print("Line 383: 'armour' in mod.applicable_items -> RETURN TRUE")
    else:
        print("Line 383: 'armour' NOT in mod.applicable_items")

    # Line 387: Check for "body_armour"
    if "body_armour" in mod_applicable_items:
        print("\nLine 387: 'body_armour' in mod.applicable_items -> enters defence filtering")
    else:
        print("\nLine 387: 'body_armour' NOT in mod.applicable_items")
        print("FALLS THROUGH TO LINE 421 -> RETURN FALSE")

print("\n--- CONCLUSION ---")
print("The mod should return FALSE because:")
print("1. 'int_armour' is NOT in mod.applicable_items")
print("2. 'body_armour' slot check doesn't apply (line 377-378 checks applicable_items, not slot requirements)")
print("3. 'armour' is NOT in mod.applicable_items")
print("4. 'body_armour' is NOT in mod.applicable_items")
print("5. Falls through to line 421 -> return False")
print("\nBUT the API is returning this mod! There must be another code path...")
