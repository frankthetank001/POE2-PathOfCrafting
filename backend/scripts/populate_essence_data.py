#!/usr/bin/env python3
"""
Script to populate the essence database with comprehensive data from CRAFTING_SYSTEM_DESIGN.md

This script creates all essences and their item-specific effects based on the complete
essence list from the design document.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.crafting import Essence, EssenceItemEffect
from app.core.database import get_db
from sqlalchemy.orm import Session


def populate_essences():
    """Populate the database with all essence data from the design document."""

    db = next(get_db())

    # Clear existing data
    db.query(EssenceItemEffect).delete()
    db.query(Essence).delete()

    # Define all essences from the design document
    essence_data = [
        # Body essences (Life)
        {
            "name": "Lesser Essence of the Body",
            "tier": "lesser",
            "type": "body",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "Armour", "modifier_type": "prefix", "text": "+(30-39) to maximum Life", "min": 30, "max": 39},
                {"item_type": "Belt", "modifier_type": "prefix", "text": "+(30-39) to maximum Life", "min": 30, "max": 39},
                {"item_type": "Jewellery", "modifier_type": "prefix", "text": "+(20-29) to maximum Life", "min": 20, "max": 29},
            ]
        },
        {
            "name": "Essence of the Body",
            "tier": "normal",
            "type": "body",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "Belt", "modifier_type": "prefix", "text": "+(85-99) to maximum Life", "min": 85, "max": 99},
                {"item_type": "Body Armour", "modifier_type": "prefix", "text": "+(85-99) to maximum Life", "min": 85, "max": 99},
                {"item_type": "Helmet", "modifier_type": "prefix", "text": "+(85-99) to maximum Life", "min": 85, "max": 99},
                {"item_type": "Shield", "modifier_type": "prefix", "text": "+(85-99) to maximum Life", "min": 85, "max": 99},
                {"item_type": "Amulet", "modifier_type": "prefix", "text": "+(70-84) to maximum Life", "min": 70, "max": 84},
                {"item_type": "Boots", "modifier_type": "prefix", "text": "+(70-84) to maximum Life", "min": 70, "max": 84},
                {"item_type": "Gloves", "modifier_type": "prefix", "text": "+(70-84) to maximum Life", "min": 70, "max": 84},
                {"item_type": "Ring", "modifier_type": "prefix", "text": "+(70-84) to maximum Life", "min": 70, "max": 84},
            ]
        },
        {
            "name": "Greater Essence of the Body",
            "tier": "greater",
            "type": "body",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "Belt", "modifier_type": "prefix", "text": "+(100-119) to maximum Life", "min": 100, "max": 119},
                {"item_type": "Body Armour", "modifier_type": "prefix", "text": "+(100-119) to maximum Life", "min": 100, "max": 119},
                {"item_type": "Helmet", "modifier_type": "prefix", "text": "+(100-119) to maximum Life", "min": 100, "max": 119},
                {"item_type": "Shield", "modifier_type": "prefix", "text": "+(100-119) to maximum Life", "min": 100, "max": 119},
                {"item_type": "Amulet", "modifier_type": "prefix", "text": "+(85-99) to maximum Life", "min": 85, "max": 99},
                {"item_type": "Boots", "modifier_type": "prefix", "text": "+(85-99) to maximum Life", "min": 85, "max": 99},
                {"item_type": "Gloves", "modifier_type": "prefix", "text": "+(85-99) to maximum Life", "min": 85, "max": 99},
            ]
        },
        {
            "name": "Perfect Essence of the Body",
            "tier": "perfect",
            "type": "body",
            "mechanic": "remove_add_rare",
            "effects": [
                {"item_type": "Body Armour", "modifier_type": "prefix", "text": "(8-10)% increased maximum Life", "min": 8, "max": 10},
            ]
        },

        # Mind essences (Mana)
        {
            "name": "Lesser Essence of the Mind",
            "tier": "lesser",
            "type": "mind",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "Belt", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
                {"item_type": "Boots", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
                {"item_type": "Gloves", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
                {"item_type": "Helmet", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
                {"item_type": "Jewellery", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
            ]
        },
        {
            "name": "Essence of the Mind",
            "tier": "normal",
            "type": "mind",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "Belt", "modifier_type": "prefix", "text": "+(65-79) to maximum Mana", "min": 65, "max": 79},
                {"item_type": "Boots", "modifier_type": "prefix", "text": "+(65-79) to maximum Mana", "min": 65, "max": 79},
                {"item_type": "Gloves", "modifier_type": "prefix", "text": "+(65-79) to maximum Mana", "min": 65, "max": 79},
                {"item_type": "Helmet", "modifier_type": "prefix", "text": "+(65-79) to maximum Mana", "min": 65, "max": 79},
                {"item_type": "Jewellery", "modifier_type": "prefix", "text": "+(80-89) to maximum Mana", "min": 80, "max": 89},
            ]
        },
        {
            "name": "Greater Essence of the Mind",
            "tier": "greater",
            "type": "mind",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "Belt", "modifier_type": "prefix", "text": "+(80-89) to maximum Mana", "min": 80, "max": 89},
                {"item_type": "Boots", "modifier_type": "prefix", "text": "+(80-89) to maximum Mana", "min": 80, "max": 89},
                {"item_type": "Gloves", "modifier_type": "prefix", "text": "+(80-89) to maximum Mana", "min": 80, "max": 89},
                {"item_type": "Helmet", "modifier_type": "prefix", "text": "+(80-89) to maximum Mana", "min": 80, "max": 89},
                {"item_type": "Jewellery", "modifier_type": "prefix", "text": "+(90-104) to maximum Mana", "min": 90, "max": 104},
            ]
        },
        {
            "name": "Perfect Essence of the Mind",
            "tier": "perfect",
            "type": "mind",
            "mechanic": "remove_add_rare",
            "effects": [
                {"item_type": "Ring", "modifier_type": "prefix", "text": "(4-6)% increased maximum Mana", "min": 4, "max": 6},
            ]
        },

        # Enhancement essences (Defense)
        {
            "name": "Lesser Essence of Enhancement",
            "tier": "lesser",
            "type": "enhancement",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "Armour", "modifier_type": "prefix", "text": "(27-42)% increased Armour, Evasion or Energy Shield", "min": 27, "max": 42},
            ]
        },
        {
            "name": "Essence of Enhancement",
            "tier": "normal",
            "type": "enhancement",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "Armour", "modifier_type": "prefix", "text": "(56-67)% increased Armour, Evasion or Energy Shield", "min": 56, "max": 67},
            ]
        },
        {
            "name": "Greater Essence of Enhancement",
            "tier": "greater",
            "type": "enhancement",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "Armour", "modifier_type": "prefix", "text": "(68-79)% increased Armour, Evasion or Energy Shield", "min": 68, "max": 79},
            ]
        },
        {
            "name": "Perfect Essence of Enhancement",
            "tier": "perfect",
            "type": "enhancement",
            "mechanic": "remove_add_rare",
            "effects": [
                {"item_type": "Amulet", "modifier_type": "prefix", "text": "(20-30)% increased Global Defences", "min": 20, "max": 30},
            ]
        },

        # Abrasion essences (Physical Damage)
        {
            "name": "Lesser Essence of Abrasion",
            "tier": "lesser",
            "type": "abrasion",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "One Handed Melee Weapon", "modifier_type": "prefix", "text": "Adds (4-6) to (7-11) Physical Damage", "min": 4, "max": 11},
                {"item_type": "Bow", "modifier_type": "prefix", "text": "Adds (4-6) to (7-11) Physical Damage", "min": 4, "max": 11},
                {"item_type": "Two Handed Melee Weapon", "modifier_type": "prefix", "text": "Adds (5-8) to (10-15) Physical Damage", "min": 5, "max": 15},
                {"item_type": "Crossbow", "modifier_type": "prefix", "text": "Adds (5-8) to (10-15) Physical Damage", "min": 5, "max": 15},
            ]
        },
        {
            "name": "Essence of Abrasion",
            "tier": "normal",
            "type": "abrasion",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "One Handed Melee Weapon", "modifier_type": "prefix", "text": "Adds (10-15) to (18-26) Physical Damage", "min": 10, "max": 26},
                {"item_type": "Bow", "modifier_type": "prefix", "text": "Adds (10-15) to (18-26) Physical Damage", "min": 10, "max": 26},
                {"item_type": "Two Handed Melee Weapon", "modifier_type": "prefix", "text": "Adds (14-21) to (25-37) Physical Damage", "min": 14, "max": 37},
                {"item_type": "Crossbow", "modifier_type": "prefix", "text": "Adds (14-21) to (25-37) Physical Damage", "min": 14, "max": 37},
            ]
        },
        {
            "name": "Greater Essence of Abrasion",
            "tier": "greater",
            "type": "abrasion",
            "mechanic": "magic_to_rare",
            "effects": [
                {"item_type": "One Handed Melee Weapon", "modifier_type": "prefix", "text": "Adds (16-24) to (28-42) Physical Damage", "min": 16, "max": 42},
                {"item_type": "Bow", "modifier_type": "prefix", "text": "Adds (16-24) to (28-42) Physical Damage", "min": 16, "max": 42},
                {"item_type": "Two Handed Melee Weapon", "modifier_type": "prefix", "text": "Adds (23-35) to (39-59) Physical Damage", "min": 23, "max": 59},
                {"item_type": "Crossbow", "modifier_type": "prefix", "text": "Adds (23-35) to (39-59) Physical Damage", "min": 23, "max": 59},
            ]
        },
        {
            "name": "Perfect Essence of Abrasion",
            "tier": "perfect",
            "type": "abrasion",
            "mechanic": "remove_add_rare",
            "effects": [
                {"item_type": "One Handed Melee Weapon", "modifier_type": "prefix", "text": "Gain (15-20)% of Damage as Extra Physical Damage", "min": 15, "max": 20},
                {"item_type": "Bow", "modifier_type": "prefix", "text": "Gain (15-20)% of Damage as Extra Physical Damage", "min": 15, "max": 20},
                {"item_type": "Two Handed Melee Weapon", "modifier_type": "prefix", "text": "Gain (25-33)% of Damage as Extra Physical Damage", "min": 25, "max": 33},
                {"item_type": "Crossbow", "modifier_type": "prefix", "text": "Gain (25-33)% of Damage as Extra Physical Damage", "min": 25, "max": 33},
            ]
        },

        # Corrupted essences
        {
            "name": "Essence of Hysteria",
            "tier": "corrupted",
            "type": "hysteria",
            "mechanic": "remove_add_rare",
            "effects": [
                {"item_type": "Helmet", "modifier_type": "prefix", "text": "+1 to Level of all Minion Skills", "min": 1, "max": 1},
                {"item_type": "Body Armour", "modifier_type": "prefix", "text": "(64-97) to (97-145) Physical Thorns damage", "min": 64, "max": 145},
                {"item_type": "Gloves", "modifier_type": "suffix", "text": "(25-29)% increased Critical Damage Bonus", "min": 25, "max": 29},
                {"item_type": "Boots", "modifier_type": "suffix", "text": "30% increased Movement Speed", "min": 30, "max": 30},
                {"item_type": "Ring", "modifier_type": "suffix", "text": "(50-59)% increased Mana Regeneration Rate", "min": 50, "max": 59},
                {"item_type": "Amulet", "modifier_type": "prefix", "text": "(19-21)% of Damage taken Recouped as Life", "min": 19, "max": 21},
                {"item_type": "Belt", "modifier_type": "prefix", "text": "+(254-304) to Stun Threshold", "min": 254, "max": 304},
                {"item_type": "Shield", "modifier_type": "suffix", "text": "(20-24)% increased Block chance", "min": 20, "max": 24},
                {"item_type": "Quiver", "modifier_type": "suffix", "text": "(43-50)% increased Damage with Bow Skills", "min": 43, "max": 50},
                {"item_type": "Focus", "modifier_type": "suffix", "text": "(41-45)% increased Energy Shield Recharge Rate", "min": 41, "max": 45},
            ]
        },
        {
            "name": "Essence of Delirium",
            "tier": "corrupted",
            "type": "delirium",
            "mechanic": "remove_add_rare",
            "effects": [
                {"item_type": "Body Armour", "modifier_type": "prefix", "text": "Allocates a random Notable Passive Skill", "min": 1, "max": 1},
            ]
        },
        {
            "name": "Essence of Horror",
            "tier": "corrupted",
            "type": "horror",
            "mechanic": "remove_add_rare",
            "effects": [
                {"item_type": "Gloves", "modifier_type": "prefix", "text": "100% increased effect of Socketed Items", "min": 100, "max": 100},
                {"item_type": "Boots", "modifier_type": "prefix", "text": "100% increased effect of Socketed Items", "min": 100, "max": 100},
            ]
        },
        {
            "name": "Essence of Insanity",
            "tier": "corrupted",
            "type": "insanity",
            "mechanic": "remove_add_rare",
            "effects": [
                {"item_type": "Belt", "modifier_type": "prefix", "text": "On Corruption, Item gains two Enchantments", "min": 1, "max": 1},
            ]
        },
        {
            "name": "Essence of the Abyss",
            "tier": "corrupted",
            "type": "abyss",
            "mechanic": "remove_add_rare",
            "effects": [
                {"item_type": "Equipment", "modifier_type": "prefix", "text": "Mark of the Abyssal Lord", "min": 1, "max": 1},
            ]
        },
    ]

    # Create essences and their effects
    for essence_data_item in essence_data:
        # Create essence
        essence = Essence(
            name=essence_data_item["name"],
            essence_tier=essence_data_item["tier"],
            essence_type=essence_data_item["type"],
            mechanic=essence_data_item["mechanic"],
            stack_size=10
        )
        db.add(essence)
        db.flush()  # Get the ID

        # Create item effects
        for effect_data in essence_data_item["effects"]:
            effect = EssenceItemEffect(
                essence_id=essence.id,
                item_type=effect_data["item_type"],
                modifier_type=effect_data["modifier_type"],
                effect_text=effect_data["text"],
                value_min=effect_data.get("min"),
                value_max=effect_data.get("max")
            )
            db.add(effect)

    db.commit()
    print(f"Successfully populated {len(essence_data)} essences with their item-specific effects")


if __name__ == "__main__":
    populate_essences()