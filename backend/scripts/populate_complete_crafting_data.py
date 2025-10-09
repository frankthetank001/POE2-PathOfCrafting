#!/usr/bin/env python3
"""
Complete Crafting Data Population Script

Loads ALL crafting data from source_data JSON files:
- Base items and modifiers
- Currency configurations
- Essences with item effects
- Omens with rules
- Desecration bones
- Desecrated modifiers

This script loads from the comprehensive JSON reference files.
"""

import sys
import os
import json

# Change to backend directory to ensure database is created there
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(backend_dir)
sys.path.insert(0, backend_dir)

from app.models.crafting import (
    BaseItem, Modifier, CurrencyConfig, Essence, EssenceItemEffect,
    Omen, OmenRule, DesecrationBone
)
from app.models.base import get_db
from sqlalchemy.orm import Session


def get_json_path(filename: str) -> str:
    """Get path to JSON file in source_data directory."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "source_data",
        filename
    )


def clear_existing_data(db: Session):
    """Clear all existing crafting data."""
    print("Clearing existing crafting data...")

    # Clear in dependency order
    db.query(EssenceItemEffect).delete()
    db.query(OmenRule).delete()

    db.query(Essence).delete()
    db.query(Omen).delete()
    db.query(DesecrationBone).delete()
    db.query(CurrencyConfig).delete()
    db.query(Modifier).delete()
    db.query(BaseItem).delete()

    db.commit()
    print("Cleared existing data")


def load_base_items(db: Session):
    """Load base items from JSON file."""
    json_path = get_json_path("generated_item_bases.json")

    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found - skipping base items")
        return

    with open(json_path, 'r') as f:
        items_data = json.load(f)

    print(f"Loading {len(items_data)} base items...")

    added_count = 0
    seen_names = set()

    for item_data in items_data:
        item_name = item_data["name"]

        # Skip if we've already seen this name in this batch
        if item_name in seen_names:
            continue

        seen_names.add(item_name)

        # Check if item already exists in database
        existing = db.query(BaseItem).filter(BaseItem.name == item_name).first()
        if existing:
            continue

        base_item = BaseItem(
            name=item_name,
            category=item_data["category"],
            slot=item_data["slot"],
            attribute_requirements=item_data.get("attribute_requirements", []),
            default_ilvl=item_data.get("default_ilvl", 1),
            description=item_data.get("description"),
            base_stats=item_data.get("base_stats", {}),
            subcategory=item_data.get("subcategory"),
            required_level=item_data.get("required_level", 0),
            required_str=item_data.get("required_str", 0),
            required_dex=item_data.get("required_dex", 0),
            required_int=item_data.get("required_int", 0)
        )
        db.add(base_item)
        added_count += 1

    db.commit()
    print(f"Loaded {added_count} unique base items (from {len(items_data)} entries)")


def load_modifiers(db: Session):
    """Load base modifiers from JSON file."""
    json_path = get_json_path("generated_modifiers.json")

    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found - skipping base modifiers")
        return

    with open(json_path, 'r') as f:
        modifiers_data = json.load(f)

    print(f"Loading {len(modifiers_data)} base modifiers...")

    added_count = 0
    seen_keys = set()

    for mod_data in modifiers_data:
        # Create unique key from name, mod_type, tier, mod_group, stat_text, AND weightKey
        # (since same name/tier can have different weight conditions for different item types)
        weight_key_tuple = tuple(mod_data.get("weight_conditions", {}).get("weightKey", [])) if mod_data.get("weight_conditions") else ()
        mod_key = (
            mod_data["name"],
            mod_data["mod_type"],
            mod_data["tier"],
            mod_data.get("mod_group"),
            mod_data["stat_text"],
            weight_key_tuple  # Include weightKey to distinguish variants
        )

        # Skip if we've already seen this combination in this batch
        if mod_key in seen_keys:
            continue

        seen_keys.add(mod_key)

        # Check if modifier already exists in database
        # Compare weight_conditions as JSON string for database lookup
        existing = db.query(Modifier).filter(
            Modifier.name == mod_data["name"],
            Modifier.mod_type == mod_data["mod_type"],
            Modifier.tier == mod_data["tier"],
            Modifier.mod_group == mod_data.get("mod_group"),
            Modifier.stat_text == mod_data["stat_text"]
        ).all()

        # Further filter by weight_conditions since SQLAlchemy can't easily compare JSON
        if existing:
            for exist_mod in existing:
                exist_weight_key = tuple(exist_mod.weight_conditions.get("weightKey", [])) if exist_mod.weight_conditions else ()
                if exist_weight_key == weight_key_tuple:
                    existing = exist_mod
                    break
            else:
                existing = None
        else:
            existing = None

        if existing:
            continue

        modifier = Modifier(
            name=mod_data["name"],
            mod_type=mod_data["mod_type"],
            tier=mod_data["tier"],
            stat_text=mod_data["stat_text"],
            stat_ranges=mod_data.get("stat_ranges", []),
            stat_min=mod_data.get("stat_min"),
            stat_max=mod_data.get("stat_max"),
            required_ilvl=mod_data.get("required_ilvl", 0),
            weight=mod_data.get("weight", 1000),
            mod_group=mod_data.get("mod_group"),
            applicable_items=mod_data.get("applicable_items", []),
            tags=mod_data.get("tags", []),
            weight_conditions=mod_data.get("weight_conditions"),
            is_exclusive=mod_data.get("is_exclusive", False)
        )
        db.add(modifier)
        added_count += 1

    db.commit()
    print(f"Loaded {added_count} unique base modifiers (from {len(modifiers_data)} entries)")


def load_essence_modifiers(db: Session):
    """Load essence-specific modifiers from JSON file.

    Updates existing modifiers if they already exist (from generated_modifiers.json),
    ensuring essence_modifiers.json takes precedence.
    """
    json_path = get_json_path("essence_modifiers.json")

    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found - skipping essence modifiers")
        return

    with open(json_path, 'r') as f:
        essence_modifiers = json.load(f)

    print(f"Loading {len(essence_modifiers)} essence modifiers...")

    added_count = 0
    updated_count = 0
    seen_keys = set()

    for mod_data in essence_modifiers:
        # Create unique key from name, mod_type, tier, mod_group, stat_text, AND weightKey
        weight_key_tuple = tuple(mod_data.get("weight_conditions", {}).get("weightKey", [])) if mod_data.get("weight_conditions") else ()
        mod_key = (
            mod_data["name"],
            mod_data["mod_type"],
            mod_data["tier"],
            mod_data.get("mod_group"),
            mod_data["stat_text"],
            weight_key_tuple  # Include weightKey to distinguish variants
        )

        # Skip if we've already seen this combination in this batch
        if mod_key in seen_keys:
            continue

        seen_keys.add(mod_key)

        # Check if modifier already exists in database
        existing = db.query(Modifier).filter(
            Modifier.name == mod_data["name"],
            Modifier.mod_type == mod_data["mod_type"],
            Modifier.tier == mod_data["tier"],
            Modifier.mod_group == mod_data.get("mod_group"),
            Modifier.stat_text == mod_data["stat_text"]
        ).all()

        # Further filter by weight_conditions
        if existing:
            for exist_mod in existing:
                exist_weight_key = tuple(exist_mod.weight_conditions.get("weightKey", [])) if exist_mod.weight_conditions else ()
                if exist_weight_key == weight_key_tuple:
                    existing = exist_mod
                    break
            else:
                existing = None
        else:
            existing = None

        if existing:
            # Update existing modifier with essence data
            existing.stat_ranges = mod_data.get("stat_ranges", [])
            existing.stat_min = mod_data.get("stat_min")
            existing.stat_max = mod_data.get("stat_max")
            existing.required_ilvl = mod_data.get("required_ilvl", 0)
            existing.weight = mod_data.get("weight", 1000)
            existing.applicable_items = mod_data.get("applicable_items", [])
            existing.tags = mod_data.get("tags", [])
            existing.weight_conditions = mod_data.get("weight_conditions")
            existing.is_exclusive = mod_data.get("is_exclusive", True)
            updated_count += 1
        else:
            # Add new modifier
            modifier = Modifier(
                name=mod_data["name"],
                mod_type=mod_data["mod_type"],
                tier=mod_data["tier"],
                stat_text=mod_data["stat_text"],
                stat_ranges=mod_data.get("stat_ranges", []),
                stat_min=mod_data.get("stat_min"),
                stat_max=mod_data.get("stat_max"),
                required_ilvl=mod_data.get("required_ilvl", 0),
                weight=mod_data.get("weight", 1000),
                mod_group=mod_data.get("mod_group"),
                applicable_items=mod_data.get("applicable_items", []),
                tags=mod_data.get("tags", []),
                weight_conditions=mod_data.get("weight_conditions"),
                is_exclusive=mod_data.get("is_exclusive", True)  # Default to True for essence mods
            )
            db.add(modifier)
            added_count += 1

    db.commit()
    print(f"Loaded {added_count} new essence modifiers, updated {updated_count} existing modifiers (from {len(essence_modifiers)} entries)")


def load_desecrated_modifiers(db: Session):
    """Load desecrated modifiers from JSON file."""
    json_path = get_json_path("desecrated_modifiers.json")

    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found - skipping desecrated modifiers")
        return

    with open(json_path, 'r') as f:
        desecrated_modifiers = json.load(f)

    print(f"Loading {len(desecrated_modifiers)} desecrated modifiers...")

    for mod_data in desecrated_modifiers:
        modifier = Modifier(
            name=mod_data["name"],
            mod_type=mod_data["mod_type"],
            tier=mod_data["tier"],
            stat_text=mod_data["stat_text"],
            stat_ranges=mod_data.get("stat_ranges", []),
            stat_min=mod_data.get("stat_min"),
            stat_max=mod_data.get("stat_max"),
            required_ilvl=mod_data["required_ilvl"],
            weight=mod_data["weight"],
            mod_group=mod_data["mod_group"],
            applicable_items=mod_data["applicable_items"],
            tags=mod_data["tags"],
            weight_conditions=mod_data.get("weight_conditions"),
            is_exclusive=mod_data["is_exclusive"]
        )
        db.add(modifier)

    db.commit()
    print(f"Loaded {len(desecrated_modifiers)} desecrated modifiers")

    # Summary by item type
    item_counts = {}
    for mod in desecrated_modifiers:
        for item in mod["applicable_items"]:
            item_counts[item] = item_counts.get(item, 0) + 1

    print("Desecrated modifiers per item type:")
    for item, count in sorted(item_counts.items()):
        print(f"  {item}: {count} modifiers")


def load_currency_configs(db: Session):
    """Load currency configurations from JSON file."""
    json_path = get_json_path("currency_configs.json")

    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found - skipping currency configs")
        return

    with open(json_path, 'r') as f:
        currency_data = json.load(f)

    print(f"Loading {len(currency_data)} currency configurations...")

    for config_data in currency_data:
        currency_config = CurrencyConfig(
            name=config_data["name"],
            currency_type=config_data["currency_type"],
            tier=config_data.get("tier"),
            rarity=config_data["rarity"],
            stack_size=config_data.get("stack_size", 20),
            mechanic_class=config_data["mechanic_class"],
            config_data=config_data.get("config_data", {})
        )
        db.add(currency_config)

    db.commit()
    print(f"Loaded {len(currency_data)} currency configurations")


def load_essences(db: Session):
    """Load essences and their effects from JSON files."""
    # Load essences
    essences_path = get_json_path("essences.json")
    effects_path = get_json_path("essence_item_effects.json")

    if not os.path.exists(essences_path):
        print(f"Warning: {essences_path} not found - skipping essences")
        return

    with open(essences_path, 'r') as f:
        essences_data = json.load(f)

    print(f"Loading {len(essences_data)} essences...")

    for essence_data in essences_data:
        essence = Essence(
            name=essence_data["name"],
            essence_tier=essence_data["essence_tier"],
            essence_type=essence_data["essence_type"],
            mechanic=essence_data["mechanic"],
            stack_size=essence_data.get("stack_size", 10)
        )
        db.add(essence)

    db.commit()

    # Load essence effects if available
    if os.path.exists(effects_path):
        with open(effects_path, 'r') as f:
            effects_data = json.load(f)

        print(f"Loading {len(effects_data)} essence item effects...")

        for effect_data in effects_data:
            # Find the essence by name
            essence = db.query(Essence).filter(Essence.name == effect_data["essence_name"]).first()
            if essence:
                effect = EssenceItemEffect(
                    essence_id=essence.id,
                    item_type=effect_data["item_type"],
                    modifier_type=effect_data["modifier_type"],
                    effect_text=effect_data["effect_text"],
                    value_min=effect_data.get("value_min"),
                    value_max=effect_data.get("value_max")
                )
                db.add(effect)

        db.commit()
        print(f"Loaded {len(effects_data)} essence item effects")

    print(f"Completed loading essences and effects")


def load_omens(db: Session):
    """Load omens from JSON file."""
    json_path = get_json_path("omens.json")

    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found - skipping omens")
        return

    with open(json_path, 'r') as f:
        omens_data = json.load(f)

    print(f"Loading {len(omens_data)} omens...")

    for omen_data in omens_data:
        omen = Omen(
            name=omen_data["name"],
            effect_description=omen_data["effect_description"],
            affected_currency=omen_data["affected_currency"],
            effect_type=omen_data.get("effect_type", "standard"),  # Default to "standard" if not specified
            stack_size=omen_data.get("stack_size", 10)
        )
        db.add(omen)

    db.commit()

    # Load omen rules if they exist in the data
    rules_count = 0
    for omen_data in omens_data:
        if "rules" in omen_data:
            omen = db.query(Omen).filter(Omen.name == omen_data["name"]).first()
            if omen:
                for rule_data in omen_data["rules"]:
                    rule = OmenRule(
                        omen_id=omen.id,
                        rule_type=rule_data["rule_type"],
                        rule_value=rule_data.get("rule_value"),
                        priority=rule_data.get("priority", 0)
                    )
                    db.add(rule)
                    rules_count += 1

    if rules_count > 0:
        db.commit()
        print(f"Loaded {rules_count} omen rules")

    print(f"Completed loading {len(omens_data)} omens")


def load_desecration_bones(db: Session):
    """Load desecration bones from JSON file."""
    json_path = get_json_path("desecration_bones.json")

    if not os.path.exists(json_path):
        print(f"Warning: {json_path} not found - skipping desecration bones")
        return

    with open(json_path, 'r') as f:
        bones_data = json.load(f)

    print(f"Loading {len(bones_data)} desecration bones...")

    for bone_data in bones_data:
        bone = DesecrationBone(
            name=bone_data["name"],
            bone_type=bone_data["bone_type"],
            bone_part=bone_data["bone_part"],
            mechanic=bone_data.get("mechanic", "add_desecrated_mod"),  # Default mechanic
            stack_size=bone_data.get("stack_size", 20),
            applicable_items=bone_data.get("applicable_items", []),
            min_modifier_level=bone_data.get("min_modifier_level"),
            max_item_level=bone_data.get("max_item_level"),
            function_description=bone_data.get("function_description")
        )
        db.add(bone)

    db.commit()
    print(f"Loaded {len(bones_data)} desecration bones")


def main():
    """Main function to populate ALL crafting data from JSON files."""
    print(f"Working directory: {os.getcwd()}")
    print("Starting COMPLETE crafting data population from JSON files...")
    print("Loading all data from backend/source_data/")

    try:
        db = next(get_db())

        # Clear existing data
        clear_existing_data(db)

        # Load all data from JSON files
        load_base_items(db)
        load_modifiers(db)
        load_essence_modifiers(db)
        load_desecrated_modifiers(db)
        load_currency_configs(db)
        load_essences(db)
        load_omens(db)
        load_desecration_bones(db)

        # Get final counts
        base_item_count = db.query(BaseItem).count()
        modifier_count = db.query(Modifier).count()
        currency_count = db.query(CurrencyConfig).count()
        essence_count = db.query(Essence).count()
        omen_count = db.query(Omen).count()
        bone_count = db.query(DesecrationBone).count()

        print("\n" + "="*50)
        print("COMPLETE CRAFTING DATA LOADED SUCCESSFULLY!")
        print("="*50)
        print(f"Base Items: {base_item_count}")
        print(f"Modifiers: {modifier_count} (including desecrated)")
        print(f"Currency Configs: {currency_count}")
        print(f"Essences: {essence_count}")
        print(f"Omens: {omen_count}")
        print(f"Desecration Bones: {bone_count}")
        print("="*50)
        print("The comprehensive PoE2 crafting system is ready!")

    except Exception as e:
        print(f"\nError populating complete crafting data: {e}")
        raise


if __name__ == "__main__":
    main()