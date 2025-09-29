"""
Template script for adding desecrated modifiers from screenshots.

Usage:
1. Copy this template for each item type
2. Fill in the modifiers from the screenshot
3. Run the script to add them to the database

Current status:
✅ body_armour - 10 suffix modifiers (shared with boots/charms where applicable)
✅ boots - shares all 10 modifiers with body_armour
✅ charm - 6 shared + 9 unique = 15 total suffix modifiers

Still needed:
- gloves
- helmet
- amulet (prefixes + suffixes)
- belt (prefixes + suffixes)
- ring (prefixes + suffixes)
- focus (prefixes + suffixes)
- quiver (prefixes + suffixes)
- shield (suffixes)
- All weapon types (wand, claw, dagger, flail, etc.)
"""

import sqlite3
import json

# Template for adding modifiers for a specific item type
def add_modifiers_for_item_type(item_type, modifiers_data):
    """
    Add desecrated modifiers for a specific item type.

    Args:
        item_type (str): The item category (e.g., 'gloves', 'helmet', etc.)
        modifiers_data (list): List of modifier dictionaries
    """

    conn = sqlite3.connect('poe2tradecraft.db')
    cursor = conn.cursor()

    print(f'Adding desecrated modifiers for {item_type}...')

    for mod_data in modifiers_data:
        # First check if an identical modifier already exists
        cursor.execute('''
            SELECT id, applicable_items
            FROM modifiers
            WHERE stat_text = ? AND tags LIKE '%desecrated_only%'
        ''', (mod_data['stat_text'],))

        existing = cursor.fetchone()

        if existing:
            # Modifier exists, update applicable_items to include this item type
            mod_id, applicable_items_str = existing
            applicable_items = json.loads(applicable_items_str)

            if item_type not in applicable_items:
                applicable_items.append(item_type)
                cursor.execute('''
                    UPDATE modifiers
                    SET applicable_items = ?
                    WHERE id = ?
                ''', (json.dumps(applicable_items), mod_id))
                print(f'  Updated existing: {mod_data["stat_text"]} (now applies to {applicable_items})')
            else:
                print(f'  Already exists: {mod_data["stat_text"]}')
        else:
            # New modifier, insert it
            cursor.execute('''
                INSERT INTO modifiers (
                    name, mod_type, tier, stat_text, stat_min, stat_max,
                    required_ilvl, weight, mod_group, applicable_items, tags, is_exclusive
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                mod_data['name'], mod_data['mod_type'], mod_data['tier'],
                mod_data['stat_text'], mod_data['stat_min'], mod_data['stat_max'],
                mod_data['required_ilvl'], mod_data['weight'], mod_data['mod_group'],
                json.dumps(mod_data['applicable_items']), json.dumps(mod_data['tags']),
                mod_data['is_exclusive']
            ))
            print(f'  Added new: {mod_data["stat_text"]}')

    conn.commit()
    conn.close()
    print(f'Completed adding modifiers for {item_type}!')

# Example usage for gloves (you would fill this in from the screenshot):
# gloves_modifiers = [
#     {
#         'name': 'Desecrated Example Modifier',
#         'mod_type': 'suffix',
#         'tier': 1,
#         'stat_text': 'Example modifier text',
#         'stat_min': 10.0,
#         'stat_max': 20.0,
#         'required_ilvl': 65,
#         'weight': 1,
#         'mod_group': 'example_group',
#         'applicable_items': ['gloves'],
#         'tags': ['desecrated_only', 'example_tag'],
#         'is_exclusive': 1
#     }
# ]
#
# add_modifiers_for_item_type('gloves', gloves_modifiers)

print("Template ready! Use this to systematically add remaining desecrated modifiers.")
print("The system will automatically:")
print("1. Detect if modifiers already exist (shared modifiers)")
print("2. Add new item types to existing modifiers")
print("3. Create new modifiers for unique effects")