#!/usr/bin/env python3
"""
Create Complete Desecrated Modifier Dataset

This script creates the comprehensive desecrated modifier system from all the screenshots.
It identifies shared modifiers and applies them to multiple item types where appropriate.
"""

import json
import os

def create_desecrated_modifiers():
    """Create the complete desecrated modifier dataset."""

    # Shared modifiers that appear on multiple item types
    shared_modifiers = {
        # Shared attribute modifiers
        "dex_int_attributes": {
            "name": "+(9-15) to Dexterity and Intelligence",
            "mod_type": "suffix",
            "tier": 1,
            "stat_text": "+(9-15) to Dexterity and Intelligence",
            "stat_min": 9,
            "stat_max": 15,
            "required_ilvl": 65,
            "weight": 1,
            "mod_group": "dual_attributes",
            "applicable_items": ["body_armour", "boots", "charm"],
            "tags": ["desecrated_only", "attribute", "kurgal"],
            "is_exclusive": True
        },
        "str_dex_attributes": {
            "name": "+(9-15) to Strength and Dexterity",
            "mod_type": "suffix",
            "tier": 1,
            "stat_text": "+(9-15) to Strength and Dexterity",
            "stat_min": 9,
            "stat_max": 15,
            "required_ilvl": 65,
            "weight": 1,
            "mod_group": "dual_attributes",
            "applicable_items": ["body_armour", "boots", "charm"],
            "tags": ["desecrated_only", "attribute", "ulaman"],
            "is_exclusive": True
        },
        "str_int_attributes": {
            "name": "+(9-15) to Strength and Intelligence",
            "mod_type": "suffix",
            "tier": 1,
            "stat_text": "+(9-15) to Strength and Intelligence",
            "stat_min": 9,
            "stat_max": 15,
            "required_ilvl": 65,
            "weight": 1,
            "mod_group": "dual_attributes",
            "applicable_items": ["body_armour", "boots", "charm"],
            "tags": ["desecrated_only", "attribute", "amanamu"],
            "is_exclusive": True
        },
        # Shared resistance modifiers
        "cold_chaos_resistance": {
            "name": "+(13-17)% to Cold and Chaos Resistances",
            "mod_type": "suffix",
            "tier": 1,
            "stat_text": "+(13-17)% to Cold and Chaos Resistances",
            "stat_min": 13,
            "stat_max": 17,
            "required_ilvl": 65,
            "weight": 1,
            "mod_group": "dual_resistances",
            "applicable_items": ["body_armour", "boots", "charm"],
            "tags": ["desecrated_only", "elemental", "cold", "chaos", "resistance", "kurgal"],
            "is_exclusive": True
        },
        "fire_chaos_resistance": {
            "name": "+(13-17)% to Fire and Chaos Resistances",
            "mod_type": "suffix",
            "tier": 1,
            "stat_text": "+(13-17)% to Fire and Chaos Resistances",
            "stat_min": 13,
            "stat_max": 17,
            "required_ilvl": 65,
            "weight": 1,
            "mod_group": "dual_resistances",
            "applicable_items": ["body_armour", "boots", "charm"],
            "tags": ["desecrated_only", "elemental", "fire", "chaos", "resistance", "amanamu"],
            "is_exclusive": True
        },
        "lightning_chaos_resistance": {
            "name": "+(13-17)% to Lightning and Chaos Resistances",
            "mod_type": "suffix",
            "tier": 1,
            "stat_text": "+(13-17)% to Lightning and Chaos Resistances",
            "stat_min": 13,
            "stat_max": 17,
            "required_ilvl": 65,
            "weight": 1,
            "mod_group": "dual_resistances",
            "applicable_items": ["body_armour", "boots", "charm"],
            "tags": ["desecrated_only", "elemental", "lightning", "chaos", "resistance", "ulaman"],
            "is_exclusive": True
        }
    }

    # Specific modifiers per item type
    item_specific_modifiers = {
        # Body Armour & Boots specific (beyond shared ones)
        "body_armour": [
            {
                "name": "(4-9)% increased Spirit Reservation Efficiency of Skills",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(4-9)% increased Spirit Reservation Efficiency of Skills",
                "stat_min": 4,
                "stat_max": 9,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "spirit",
                "applicable_items": ["body_armour", "boots"],
                "tags": ["desecrated_only", "amanamu"],
                "is_exclusive": True
            },
            {
                "name": "(10-20)% of Damage taken Recouped as Mana",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(10-20)% of Damage taken Recouped as Mana",
                "stat_min": 10,
                "stat_max": 20,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "recoup",
                "applicable_items": ["body_armour", "boots"],
                "tags": ["desecrated_only", "life", "mana", "kurgal"],
                "is_exclusive": True
            },
            {
                "name": "(25-35)% reduced effect of Curses on you",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(25-35)% reduced effect of Curses on you",
                "stat_min": 25,
                "stat_max": 35,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "curse_protection",
                "applicable_items": ["body_armour", "boots"],
                "tags": ["desecrated_only", "caster", "curse", "amanamu"],
                "is_exclusive": True
            },
            {
                "name": "Hits have (17-25)% reduced Critical Hit Chance against you",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "Hits have (17-25)% reduced Critical Hit Chance against you",
                "stat_min": 17,
                "stat_max": 25,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "critical_protection",
                "applicable_items": ["body_armour", "boots"],
                "tags": ["desecrated_only", "critical", "ulaman"],
                "is_exclusive": True
            }
        ],

        # Charm specific modifiers (beyond shared ones)
        "charm": [
            {
                "name": "(8-12)% increased Mana Cost Efficiency if you have Dodge Rolled Recently",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(8-12)% increased Mana Cost Efficiency if you have Dodge Rolled Recently",
                "stat_min": 8,
                "stat_max": 12,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "mana_efficiency",
                "applicable_items": ["charm"],
                "tags": ["desecrated_only", "mana", "kurgal"],
                "is_exclusive": True
            },
            {
                "name": "(40-50)% increased Mana Regeneration Rate while stationary",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(40-50)% increased Mana Regeneration Rate while stationary",
                "stat_min": 40,
                "stat_max": 50,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "mana_regen",
                "applicable_items": ["charm"],
                "tags": ["desecrated_only", "mana", "kurgal"],
                "is_exclusive": True
            },
            {
                "name": "(20-30)% reduced Duration of Bleeding on You",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(20-30)% reduced Duration of Bleeding on You",
                "stat_min": 20,
                "stat_max": 30,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "ailment_duration",
                "applicable_items": ["charm"],
                "tags": ["desecrated_only", "bleed", "physical", "ailment", "kurgal"],
                "is_exclusive": True
            },
            {
                "name": "(20-30)% reduced Ignite Duration on you",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(20-30)% reduced Ignite Duration on you",
                "stat_min": 20,
                "stat_max": 30,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "ailment_duration",
                "applicable_items": ["charm"],
                "tags": ["desecrated_only", "fire", "ailment", "amanamu"],
                "is_exclusive": True
            },
            {
                "name": "(6-10)% reduced Movement Speed Penalty from using Skills while moving",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(6-10)% reduced Movement Speed Penalty from using Skills while moving",
                "stat_min": 6,
                "stat_max": 10,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "movement_penalty",
                "applicable_items": ["charm"],
                "tags": ["desecrated_only", "speed", "ulaman"],
                "is_exclusive": True
            },
            {
                "name": "(20-30)% reduced Poison Duration on you",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(20-30)% reduced Poison Duration on you",
                "stat_min": 20,
                "stat_max": 30,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "ailment_duration",
                "applicable_items": ["charm"],
                "tags": ["desecrated_only", "poison", "chaos", "ailment", "ulaman"],
                "is_exclusive": True
            },
            {
                "name": "(12-20)% reduced Slowing Potency of Debuffs on You",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "(12-20)% reduced Slowing Potency of Debuffs on You",
                "stat_min": 12,
                "stat_max": 20,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "debuff_protection",
                "applicable_items": ["charm"],
                "tags": ["desecrated_only", "amanamu"],
                "is_exclusive": True
            },
            {
                "name": "+(0.1-0.2) metres to Dodge Roll distance",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "+(0.1-0.2) metres to Dodge Roll distance",
                "stat_min": 0.1,
                "stat_max": 0.2,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "dodge_roll",
                "applicable_items": ["charm"],
                "tags": ["desecrated_only", "amanamu"],
                "is_exclusive": True
            },
            {
                "name": "Corrupted Blood cannot be inflicted on you",
                "mod_type": "suffix",
                "tier": 1,
                "stat_text": "Corrupted Blood cannot be inflicted on you",
                "stat_min": None,
                "stat_max": None,
                "required_ilvl": 65,
                "weight": 1,
                "mod_group": "corrupted_blood_immunity",
                "applicable_items": ["charm"],
                "tags": ["desecrated_only", "bleed", "physical", "ailment", "ulaman"],
                "is_exclusive": True
            }
        ]
    }

    # Combine all modifiers
    all_modifiers = []

    # Add shared modifiers
    for modifier_data in shared_modifiers.values():
        all_modifiers.append(modifier_data)

    # Add item-specific modifiers
    for item_type, modifiers in item_specific_modifiers.items():
        for modifier in modifiers:
            all_modifiers.append(modifier)

    return all_modifiers

def main():
    """Create desecrated modifier dataset and save to JSON."""
    print("Creating comprehensive desecrated modifier dataset...")

    desecrated_modifiers = create_desecrated_modifiers()

    # Ensure source_data directory exists
    os.makedirs("backend/source_data", exist_ok=True)

    # Save to JSON file
    with open("backend/source_data/desecrated_modifiers.json", "w") as f:
        json.dump(desecrated_modifiers, f, indent=2)

    print(f"Created {len(desecrated_modifiers)} desecrated modifiers")

    # Summary by item type
    item_counts = {}
    for mod in desecrated_modifiers:
        for item in mod["applicable_items"]:
            item_counts[item] = item_counts.get(item, 0) + 1

    print("\nModifiers per item type:")
    for item, count in sorted(item_counts.items()):
        print(f"  {item}: {count} modifiers")

    return desecrated_modifiers

if __name__ == "__main__":
    main()