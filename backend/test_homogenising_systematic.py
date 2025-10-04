import requests
import json

def test_homogenising_exaltation():
    """Systematically test homogenising exaltation by applying it multiple times"""

    # Start with an item with 2 suffixes: one with tags, one without
    item = {
        "base_name": "Coral Amulet",
        "base_category": "amulet",
        "rarity": "Rare",
        "item_level": 82,
        "quality": 0,
        "prefix_mods": [],
        "suffix_mods": [
            {
                "name": "of Celerity",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "25% increased Cast Speed",
                "tags": ["caster", "speed"]
            },
            {
                "name": "of Windfall",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "35% increased Rarity of Items found",
                "tags": []
            }
        ],
        "implicit_mods": [],
        "unrevealed_mods": [],
        "corrupted": False
    }

    print("="*80)
    print("SYSTEMATIC HOMOGENISING EXALTATION TEST")
    print("="*80)
    print("\nStarting item:")
    print(f"  Prefixes: {len(item['prefix_mods'])}/3")
    print(f"  Suffixes: {len(item['suffix_mods'])}/3")
    for mod in item['suffix_mods']:
        print(f"    - {mod['name']}: {mod['stat_text']} (tags: {mod['tags']})")

    # Get all existing tags for validation
    all_existing_tags = set()
    for mod in item['prefix_mods'] + item['suffix_mods']:
        if mod.get('tags'):
            all_existing_tags.update(mod['tags'])

    print(f"\nAll existing tags: {list(all_existing_tags)}")
    print("\n" + "="*80)

    # Apply homogenising exaltation 5 times
    for i in range(1, 6):
        print(f"\n### Application #{i} ###")

        response = requests.post(
            "http://localhost:8000/api/v1/crafting/simulate-with-omens",
            json={
                "item": item,
                "currency_name": "Perfect Exalted Orb",
                "omen_names": ["Omen of Homogenising Exaltation"]
            }
        )

        if response.status_code != 200:
            print(f"ERROR: Request failed with status {response.status_code}")
            print(response.text)
            break

        result = response.json()

        if not result.get('success'):
            print(f"Crafting failed: {result.get('message')}")
            break

        # Update item state
        item = result['item']

        # Find the newly added mod
        all_current_mods = item['prefix_mods'] + item['suffix_mods']

        # Determine which mod was just added (last one in the list)
        added_mod = None
        if len(item['prefix_mods']) > len(result.get('previous_prefixes', [])):
            added_mod = item['prefix_mods'][-1]
            mod_type = "prefix"
        elif len(item['suffix_mods']) > len(result.get('previous_suffixes', [])):
            added_mod = item['suffix_mods'][-1]
            mod_type = "suffix"

        print(f"Message: {result.get('message')}")
        print(f"Added {mod_type}: {added_mod['name']}")
        print(f"  Stat: {added_mod.get('stat_text', 'N/A')}")
        print(f"  Tags: {added_mod.get('tags', [])}")

        # Verify tags match
        added_tags = set(added_mod.get('tags', []))
        has_matching_tag = bool(added_tags & all_existing_tags)

        if has_matching_tag:
            matching_tags = list(added_tags & all_existing_tags)
            print(f"  ✓ VALID: Has matching tag(s): {matching_tags}")
        elif not all_existing_tags:
            print(f"  ⚠ WARNING: No existing tags to match (edge case)")
        else:
            print(f"  ✗ INVALID: No matching tags! Expected one of {list(all_existing_tags)}")

        # Update existing tags for next iteration
        if added_tags:
            all_existing_tags.update(added_tags)

        print(f"\nCurrent state:")
        print(f"  Prefixes: {len(item['prefix_mods'])}/3")
        print(f"  Suffixes: {len(item['suffix_mods'])}/3")

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)

if __name__ == "__main__":
    test_homogenising_exaltation()
