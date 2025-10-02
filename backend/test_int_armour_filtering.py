"""Test to debug why % increased Armour shows up on int_armour"""
import json

# Load modifiers
with open('backend/source_data/modifiers.json') as f:
    mods = json.load(f)

# Find a "% increased Armour" mod that should only be on str_armour
armour_mods = [m for m in mods if m.get('stat_text') == '{}% increased Armour' and 'str_armour' in m.get('applicable_items', [])]

print(f"Found {len(armour_mods)} pure '% increased Armour' mods for str_armour")
print(f"\nFirst mod details:")
print(f"  Name: {armour_mods[0]['name']}")
print(f"  Stat text: {armour_mods[0]['stat_text']}")
print(f"  Applicable items: {armour_mods[0]['applicable_items']}")

# Now check if "int_armour" is in there
if 'int_armour' in armour_mods[0]['applicable_items']:
    print("\nERROR: int_armour IS in applicable_items!")
else:
    print("\nCORRECT: int_armour is NOT in applicable_items")

# Check logic path
item_category = "int_armour"
mod_applicable_items = armour_mods[0]['applicable_items']

print(f"\n--- Simulating _is_mod_applicable_to_category logic ---")
print(f"item_category: {item_category}")
print(f"mod.applicable_items: {mod_applicable_items}")

# Line 373-374: Direct category match
if item_category in mod_applicable_items:
    print("Line 373-374: Direct match found - THIS SHOULD NOT HAPPEN!")
else:
    print("Line 373-374: No direct match (correct)")

# Line 381-384: Check for "armour" universal category
if item_category in ["int_armour", "str_armour", "dex_armour", "str_dex_armour", "str_int_armour", "dex_int_armour", "str_dex_int_armour"]:
    if "armour" in mod_applicable_items:
        print("Line 383: 'armour' found in applicable_items - MOD WOULD BE INCLUDED!")
    else:
        print("Line 383: 'armour' NOT in applicable_items (correct)")

    # Line 387: Check for body_armour
    if "body_armour" in mod_applicable_items:
        print("Line 387: 'body_armour' found - enters defence filtering logic")
    else:
        print("Line 387: 'body_armour' NOT found - skips defence filtering")

print("\n--- Checking if mod should be included ---")
# The mod should return False from _is_mod_applicable_to_category
