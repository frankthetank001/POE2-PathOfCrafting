#!/usr/bin/env python3
"""
Comprehensive Crafting Data Population Script

Populates the database with all crafting configurations from CRAFTING_SYSTEM_DESIGN.md:
- Currency configurations
- Essence data and item-specific effects
- Omen data and rules
- Desecration bones
- Modifier pools

This implements the Smart Hybrid Architecture - storing content in database
while keeping mechanics in code.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.crafting import (
    CurrencyConfig, Essence, EssenceItemEffect, Omen, OmenRule,
    DesecrationBone, ModifierPool, PoolModifier
)
from app.models.base import get_db
from sqlalchemy.orm import Session


def clear_existing_data(db: Session):
    """Clear all existing crafting data."""
    print("Clearing existing crafting data...")

    # Clear in dependency order
    db.query(EssenceItemEffect).delete()
    db.query(OmenRule).delete()
    db.query(PoolModifier).delete()

    db.query(Essence).delete()
    db.query(Omen).delete()
    db.query(DesecrationBone).delete()
    db.query(ModifierPool).delete()
    db.query(CurrencyConfig).delete()

    db.commit()
    print("Cleared existing data")


def populate_currency_configs(db: Session):
    """Populate basic currency configurations."""
    print("Populating currency configurations...")

    currencies = [
        # Basic currencies
        {
            "name": "Orb of Transmutation",
            "currency_type": "transmutation",
            "tier": None,
            "rarity": "common",
            "stack_size": 40,
            "mechanic_class": "TransmutationMechanic",
            "config_data": {"min_mods": 1, "max_mods": 2}
        },
        {
            "name": "Greater Orb of Transmutation",
            "currency_type": "transmutation",
            "tier": "greater",
            "rarity": "uncommon",
            "stack_size": 40,
            "mechanic_class": "TransmutationMechanic",
            "config_data": {"min_mods": 1, "max_mods": 2, "min_mod_level": 55}
        },
        {
            "name": "Perfect Orb of Transmutation",
            "currency_type": "transmutation",
            "tier": "perfect",
            "rarity": "rare",
            "stack_size": 40,
            "mechanic_class": "TransmutationMechanic",
            "config_data": {"min_mods": 1, "max_mods": 2, "min_mod_level": 70}
        },

        # Augmentation
        {
            "name": "Orb of Augmentation",
            "currency_type": "augmentation",
            "tier": None,
            "rarity": "common",
            "stack_size": 30,
            "mechanic_class": "AugmentationMechanic",
            "config_data": {}
        },
        {
            "name": "Greater Orb of Augmentation",
            "currency_type": "augmentation",
            "tier": "greater",
            "rarity": "uncommon",
            "stack_size": 30,
            "mechanic_class": "AugmentationMechanic",
            "config_data": {"min_mod_level": 55}
        },
        {
            "name": "Perfect Orb of Augmentation",
            "currency_type": "augmentation",
            "tier": "perfect",
            "rarity": "rare",
            "stack_size": 30,
            "mechanic_class": "AugmentationMechanic",
            "config_data": {"min_mod_level": 70}
        },

        # Alchemy
        {
            "name": "Orb of Alchemy",
            "currency_type": "alchemy",
            "tier": None,
            "rarity": "uncommon",
            "stack_size": 10,
            "mechanic_class": "AlchemyMechanic",
            "config_data": {"min_mods": 4, "max_mods": 6}
        },

        # Regal
        {
            "name": "Regal Orb",
            "currency_type": "regal",
            "tier": None,
            "rarity": "uncommon",
            "stack_size": 20,
            "mechanic_class": "RegalMechanic",
            "config_data": {}
        },
        {
            "name": "Greater Regal Orb",
            "currency_type": "regal",
            "tier": "greater",
            "rarity": "rare",
            "stack_size": 20,
            "mechanic_class": "RegalMechanic",
            "config_data": {"min_mod_level": 55}
        },
        {
            "name": "Perfect Regal Orb",
            "currency_type": "regal",
            "tier": "perfect",
            "rarity": "rare",
            "stack_size": 20,
            "mechanic_class": "RegalMechanic",
            "config_data": {"min_mod_level": 70}
        },

        # Exalted
        {
            "name": "Exalted Orb",
            "currency_type": "exalted",
            "tier": None,
            "rarity": "rare",
            "stack_size": 20,
            "mechanic_class": "ExaltedMechanic",
            "config_data": {}
        },
        {
            "name": "Greater Exalted Orb",
            "currency_type": "exalted",
            "tier": "greater",
            "rarity": "very_rare",
            "stack_size": 20,
            "mechanic_class": "ExaltedMechanic",
            "config_data": {"min_mod_level": 55}
        },
        {
            "name": "Perfect Exalted Orb",
            "currency_type": "exalted",
            "tier": "perfect",
            "rarity": "very_rare",
            "stack_size": 20,
            "mechanic_class": "ExaltedMechanic",
            "config_data": {"min_mod_level": 70}
        },

        # Chaos
        {
            "name": "Chaos Orb",
            "currency_type": "chaos",
            "tier": None,
            "rarity": "rare",
            "stack_size": 20,
            "mechanic_class": "ChaosMechanic",
            "config_data": {}
        },
        {
            "name": "Greater Chaos Orb",
            "currency_type": "chaos",
            "tier": "greater",
            "rarity": "very_rare",
            "stack_size": 20,
            "mechanic_class": "ChaosMechanic",
            "config_data": {"min_mod_level": 55}
        },
        {
            "name": "Perfect Chaos Orb",
            "currency_type": "chaos",
            "tier": "perfect",
            "rarity": "very_rare",
            "stack_size": 20,
            "mechanic_class": "ChaosMechanic",
            "config_data": {"min_mod_level": 70}
        },

        # Divine
        {
            "name": "Divine Orb",
            "currency_type": "divine",
            "tier": None,
            "rarity": "very_rare",
            "stack_size": 10,
            "mechanic_class": "DivineMechanic",
            "config_data": {}
        },
    ]

    for currency_data in currencies:
        currency = CurrencyConfig(**currency_data)
        db.add(currency)

    db.commit()
    print(f"Created {len(currencies)} currency configurations")


def populate_essence_data(db: Session):
    """Populate essence data from CRAFTING_SYSTEM_DESIGN.md."""
    print("Populating essence data...")

    essence_data = [
        # Body essences (Life) - from design doc
        {
            "name": "Lesser Essence of the Body",
            "essence_tier": "lesser",
            "essence_type": "body",
            "mechanic": "magic_to_rare",
            "stack_size": 10,
            "effects": [
                {"item_type": "Armour", "modifier_type": "prefix", "text": "+(30-39) to maximum Life", "min": 30, "max": 39},
                {"item_type": "Belt", "modifier_type": "prefix", "text": "+(30-39) to maximum Life", "min": 30, "max": 39},
                {"item_type": "Jewellery", "modifier_type": "prefix", "text": "+(20-29) to maximum Life", "min": 20, "max": 29},
            ]
        },
        {
            "name": "Essence of the Body",
            "essence_tier": "normal",
            "essence_type": "body",
            "mechanic": "magic_to_rare",
            "stack_size": 10,
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
            "essence_tier": "greater",
            "essence_type": "body",
            "mechanic": "magic_to_rare",
            "stack_size": 10,
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
            "essence_tier": "perfect",
            "essence_type": "body",
            "mechanic": "remove_add_rare",
            "stack_size": 10,
            "effects": [
                {"item_type": "Body Armour", "modifier_type": "prefix", "text": "(8-10)% increased maximum Life", "min": 8, "max": 10},
            ]
        },

        # Mind essences (Mana)
        {
            "name": "Lesser Essence of the Mind",
            "essence_tier": "lesser",
            "essence_type": "mind",
            "mechanic": "magic_to_rare",
            "stack_size": 10,
            "effects": [
                {"item_type": "Belt", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
                {"item_type": "Boots", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
                {"item_type": "Gloves", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
                {"item_type": "Helmet", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
                {"item_type": "Jewellery", "modifier_type": "prefix", "text": "+(25-34) to maximum Mana", "min": 25, "max": 34},
            ]
        },
        {
            "name": "Perfect Essence of the Mind",
            "essence_tier": "perfect",
            "essence_type": "mind",
            "mechanic": "remove_add_rare",
            "stack_size": 10,
            "effects": [
                {"item_type": "Ring", "modifier_type": "prefix", "text": "(4-6)% increased maximum Mana", "min": 4, "max": 6},
            ]
        },

        # Corrupted essences
        {
            "name": "Essence of Hysteria",
            "essence_tier": "corrupted",
            "essence_type": "hysteria",
            "mechanic": "remove_add_rare",
            "stack_size": 10,
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
    ]

    # Add currency configs for essences
    for essence_data_item in essence_data:
        # Create currency config
        currency_config = CurrencyConfig(
            name=essence_data_item["name"],
            currency_type="essence",
            tier=essence_data_item["essence_tier"],
            rarity="uncommon" if essence_data_item["essence_tier"] == "normal" else "rare",
            stack_size=essence_data_item["stack_size"],
            mechanic_class="EssenceMechanic",
            config_data={}
        )
        db.add(currency_config)

    # Create essences and their effects
    for essence_data_item in essence_data:
        essence = Essence(
            name=essence_data_item["name"],
            essence_tier=essence_data_item["essence_tier"],
            essence_type=essence_data_item["essence_type"],
            mechanic=essence_data_item["mechanic"],
            stack_size=essence_data_item["stack_size"]
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
    print(f"Created {len(essence_data)} essences with their item effects")


def populate_omen_data(db: Session):
    """Populate omen data from CRAFTING_SYSTEM_DESIGN.md."""
    print("Populating omen data...")

    omens_data = [
        # Chaos Orb modifiers
        {
            "name": "Omen of Whittling",
            "effect_description": "Chaos Orb removes lowest level modifier",
            "affected_currency": "Chaos Orb",
            "effect_type": "modifier_selection",
            "rules": [
                {"rule_type": "remove_lowest_tier", "rule_value": None, "priority": 1}
            ]
        },
        {
            "name": "Omen of Sinistral Erasure",
            "effect_description": "Chaos Orb removes only prefixes",
            "affected_currency": "Chaos Orb",
            "effect_type": "sinistral",
            "rules": [
                {"rule_type": "force_prefix_removal", "rule_value": None, "priority": 1}
            ]
        },
        {
            "name": "Omen of Dextral Erasure",
            "effect_description": "Chaos Orb removes only suffixes",
            "affected_currency": "Chaos Orb",
            "effect_type": "dextral",
            "rules": [
                {"rule_type": "force_suffix_removal", "rule_value": None, "priority": 1}
            ]
        },

        # Alchemy Orb modifiers
        {
            "name": "Omen of Sinistral Alchemy",
            "effect_description": "Results in maximum prefix modifiers",
            "affected_currency": "Orb of Alchemy",
            "effect_type": "sinistral",
            "rules": [
                {"rule_type": "force_max_prefixes", "rule_value": "3", "priority": 1}
            ]
        },
        {
            "name": "Omen of Dextral Alchemy",
            "effect_description": "Results in maximum suffix modifiers",
            "affected_currency": "Orb of Alchemy",
            "effect_type": "dextral",
            "rules": [
                {"rule_type": "force_max_suffixes", "rule_value": "3", "priority": 1}
            ]
        },

        # Exalted Orb modifiers
        {
            "name": "Omen of Greater Exaltation",
            "effect_description": "Adds TWO random modifiers",
            "affected_currency": "Exalted Orb",
            "effect_type": "greater",
            "rules": [
                {"rule_type": "add_two_modifiers", "rule_value": None, "priority": 1}
            ]
        },
        {
            "name": "Omen of Sinistral Exaltation",
            "effect_description": "Adds only prefix modifier",
            "affected_currency": "Exalted Orb",
            "effect_type": "sinistral",
            "rules": [
                {"rule_type": "force_prefix_addition", "rule_value": None, "priority": 1}
            ]
        },
        {
            "name": "Omen of Dextral Exaltation",
            "effect_description": "Adds only suffix modifier",
            "affected_currency": "Exalted Orb",
            "effect_type": "dextral",
            "rules": [
                {"rule_type": "force_suffix_addition", "rule_value": None, "priority": 1}
            ]
        },

        # Special omens
        {
            "name": "Omen of Corruption",
            "effect_description": "Vaal Orb always results in change",
            "affected_currency": "Vaal Orb",
            "effect_type": "guaranteed_change",
            "rules": [
                {"rule_type": "force_corruption_change", "rule_value": None, "priority": 1}
            ]
        },
        {
            "name": "Omen of the Blessed",
            "effect_description": "Divine Orb only rerolls Implicit modifiers",
            "affected_currency": "Divine Orb",
            "effect_type": "blessed",
            "rules": [
                {"rule_type": "reroll_implicits_only", "rule_value": None, "priority": 1}
            ]
        },
    ]

    for omen_data in omens_data:
        # Create omen
        omen = Omen(
            name=omen_data["name"],
            effect_description=omen_data["effect_description"],
            affected_currency=omen_data["affected_currency"],
            effect_type=omen_data["effect_type"],
            stack_size=10
        )
        db.add(omen)
        db.flush()  # Get the ID

        # Create rules
        for rule_data in omen_data["rules"]:
            rule = OmenRule(
                omen_id=omen.id,
                rule_type=rule_data["rule_type"],
                rule_value=rule_data["rule_value"],
                priority=rule_data["priority"]
            )
            db.add(rule)

    db.commit()
    print(f"Created {len(omens_data)} omens with their rules")


def populate_desecration_data(db: Session):
    """Populate desecration bone data from CRAFTING_SYSTEM_DESIGN.md."""
    print("Populating desecration data...")

    bones_data = [
        {"name": "Abyssal Jawbone", "bone_type": "jawbone", "quality": "regular"},
        {"name": "Ancient Abyssal Jawbone", "bone_type": "jawbone", "quality": "ancient"},
        {"name": "Abyssal Rib", "bone_type": "rib", "quality": "regular"},
        {"name": "Ancient Abyssal Rib", "bone_type": "rib", "quality": "ancient"},
        {"name": "Abyssal Collarbone", "bone_type": "collarbone", "quality": "regular"},
        {"name": "Ancient Abyssal Collarbone", "bone_type": "collarbone", "quality": "ancient"},
        {"name": "Abyssal Cranium", "bone_type": "cranium", "quality": "regular"},
        {"name": "Ancient Abyssal Cranium", "bone_type": "cranium", "quality": "ancient"},
        {"name": "Abyssal Vertebrae", "bone_type": "vertebrae", "quality": "regular"},
        {"name": "Ancient Abyssal Vertebrae", "bone_type": "vertebrae", "quality": "ancient"},
    ]

    for bone_data in bones_data:
        bone = DesecrationBone(
            name=bone_data["name"],
            bone_type=bone_data["bone_type"],
            quality=bone_data["quality"],
            mechanic="add_desecrated_mod",
            stack_size=20
        )
        db.add(bone)

    db.commit()
    print(f"Created {len(bones_data)} desecration bones")


def populate_modifier_pools(db: Session):
    """Populate modifier pool configurations."""
    print("Populating modifier pools...")

    pools_data = [
        {"name": "regular", "pool_type": "regular", "description": "Standard modifier pool"},
        {"name": "essence_only", "pool_type": "essence_only", "description": "Essence-exclusive modifiers"},
        {"name": "desecrated", "pool_type": "desecrated", "description": "Desecrated modifiers from bosses"},
        {"name": "corrupted", "pool_type": "corrupted", "description": "Corruption-exclusive modifiers"},
    ]

    for pool_data in pools_data:
        pool = ModifierPool(**pool_data)
        db.add(pool)

    db.commit()
    print(f"Created {len(pools_data)} modifier pools")


def main():
    """Main function to populate all crafting data."""
    print("Starting comprehensive crafting data population...")

    try:
        db = next(get_db())

        # Clear existing data
        clear_existing_data(db)

        # Populate all data
        populate_currency_configs(db)
        populate_essence_data(db)
        populate_omen_data(db)
        populate_desecration_data(db)
        populate_modifier_pools(db)

        print("\nSuccessfully populated comprehensive crafting data!")
        print("The Smart Hybrid Architecture is now ready:")
        print("- Mechanics in code (app/services/crafting/mechanics.py)")
        print("- Content in database (currencies, essences, omens, etc.)")
        print("- Unified factory (app/services/crafting/unified_factory.py)")

    except Exception as e:
        print(f"\nError populating crafting data: {e}")
        raise


if __name__ == "__main__":
    main()