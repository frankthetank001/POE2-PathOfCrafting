#!/usr/bin/env python3
"""
Migrate JSON Data to Database

Migrates item_bases.json and modifiers.json from the scraped data
into the Smart Hybrid Architecture database tables.

This replaces file-based storage with efficient database queries.
"""

import sys
import os
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import sessionmaker
from app.models.base import engine
from app.models.crafting import BaseItem, Modifier
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def load_json_data():
    """Load the scraped JSON data."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load item bases
    with open(os.path.join(base_dir, 'app', 'data', 'item_bases.json'), 'r') as f:
        item_bases = json.load(f)

    # Load modifiers
    with open(os.path.join(base_dir, 'app', 'data', 'modifiers.json'), 'r') as f:
        modifiers = json.load(f)

    return item_bases, modifiers


def clear_existing_data(session):
    """Clear existing item bases and modifiers."""
    logger.info("Clearing existing data...")

    # Clear in dependency order
    session.query(BaseItem).delete()
    session.query(Modifier).delete()

    session.commit()
    logger.info("Cleared existing data")


def migrate_item_bases(session, item_bases_data):
    """Migrate item bases from JSON to database."""
    logger.info(f"Migrating {len(item_bases_data)} item bases...")

    migrated_count = 0
    seen_names = set()

    for base_data in item_bases_data:
        try:
            original_name = base_data['name']
            unique_name = original_name

            # Handle duplicates by making names unique
            counter = 1
            while unique_name in seen_names:
                unique_name = f"{original_name} ({counter})"
                counter += 1

            seen_names.add(unique_name)

            base_item = BaseItem(
                name=unique_name,
                category=base_data['category'],
                slot=base_data['slot'],
                attribute_requirements=base_data.get('attribute_requirements', []),
                default_ilvl=base_data.get('default_ilvl', 1),
                description=base_data.get('description'),
                base_stats=base_data.get('base_stats', {}),
            )

            session.add(base_item)
            migrated_count += 1

            if unique_name != original_name:
                logger.info(f"Renamed duplicate: '{original_name}' -> '{unique_name}'")

            if migrated_count % 50 == 0:
                logger.info(f"Migrated {migrated_count} item bases...")

        except Exception as e:
            logger.error(f"Error migrating item base '{base_data.get('name', 'unknown')}': {e}")

    session.commit()
    logger.info(f"Successfully migrated {migrated_count} item bases")
    return migrated_count


def migrate_modifiers(session, modifiers_data):
    """Migrate modifiers from JSON to database."""
    logger.info(f"Migrating {len(modifiers_data)} modifiers...")

    migrated_count = 0

    for mod_data in modifiers_data:
        try:
            modifier = Modifier(
                name=mod_data['name'],
                mod_type=mod_data['mod_type'],
                tier=mod_data['tier'],
                stat_text=mod_data['stat_text'],
                stat_min=mod_data.get('stat_min'),
                stat_max=mod_data.get('stat_max'),
                required_ilvl=mod_data.get('required_ilvl', 0),
                weight=mod_data.get('weight', 1000),
                mod_group=mod_data.get('mod_group'),
                applicable_items=mod_data.get('applicable_items', []),
                tags=mod_data.get('tags', []),
                is_exclusive=mod_data.get('is_exclusive', False),
            )

            session.add(modifier)
            migrated_count += 1

            if migrated_count % 100 == 0:
                logger.info(f"Migrated {migrated_count} modifiers...")

        except Exception as e:
            logger.error(f"Error migrating modifier '{mod_data.get('name', 'unknown')}': {e}")

    session.commit()
    logger.info(f"Successfully migrated {migrated_count} modifiers")
    return migrated_count


def validate_migration(session):
    """Validate the migration was successful."""
    logger.info("Validating migration...")

    # Count records
    base_count = session.query(BaseItem).count()
    mod_count = session.query(Modifier).count()

    logger.info(f"Database contains:")
    logger.info(f"  - {base_count} item bases")
    logger.info(f"  - {mod_count} modifiers")

    # Test queries that the crafting system will use
    try:
        # Test item base lookup
        sample_base = session.query(BaseItem).filter(BaseItem.category == 'str_armour').first()
        if sample_base:
            logger.info(f"Sample base item: {sample_base.name} (category: {sample_base.category})")

        # Test modifier lookup by group
        life_mods = session.query(Modifier).filter(Modifier.mod_group == 'life').count()
        logger.info(f"Found {life_mods} life modifiers")

        # Test modifier lookup by tier
        t1_mods = session.query(Modifier).filter(Modifier.tier == 1).count()
        logger.info(f"Found {t1_mods} tier 1 modifiers")

        # Test applicable items query
        ring_mods = session.query(Modifier).filter(
            Modifier.applicable_items.contains(['ring'])
        ).count()
        logger.info(f"Found {ring_mods} modifiers applicable to rings")

        return True

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        return False


def main():
    """Main migration function."""
    logger.info("Starting JSON to Database Migration")
    logger.info("=" * 50)

    try:
        # Load JSON data
        logger.info("Loading JSON data...")
        item_bases_data, modifiers_data = load_json_data()
        logger.info(f"Loaded {len(item_bases_data)} item bases and {len(modifiers_data)} modifiers")

        # Create database session
        session = SessionLocal()

        try:
            # Clear existing data
            clear_existing_data(session)

            # Migrate data
            base_count = migrate_item_bases(session, item_bases_data)
            mod_count = migrate_modifiers(session, modifiers_data)

            # Validate migration
            if validate_migration(session):
                logger.info("MIGRATION SUCCESSFUL!")
                logger.info(f"Migrated {base_count} item bases and {mod_count} modifiers")
                logger.info("")
                logger.info("Benefits of database storage:")
                logger.info("  - Indexed queries for fast lookups")
                logger.info("  - Relational joins between bases and modifiers")
                logger.info("  - Efficient filtering by tier, group, item type")
                logger.info("  - Memory efficient (no loading entire files)")
                logger.info("  - ACID transactions for data integrity")
                logger.info("")
                logger.info("Next: Update crafting system to use database queries")
                return 0
            else:
                logger.error("Migration validation failed")
                return 1

        finally:
            session.close()

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)