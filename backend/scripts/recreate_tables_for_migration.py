#!/usr/bin/env python3
"""
Recreate Tables for Migration

Drops and recreates database tables to ensure they match the updated models
for the JSON data migration.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.base import Base, engine
from app.models.crafting import (
    BaseItem, Modifier, Currency, Essence, EssenceItemEffect,
    Omen, OmenRule, DesecrationBone, ModifierPool, PoolModifier,
    CurrencyConfig, CraftingProject
)


def recreate_tables():
    """Drop and recreate all database tables."""
    print("Dropping existing tables...")

    try:
        # Drop all tables
        Base.metadata.drop_all(bind=engine)
        print("Successfully dropped all tables")
    except Exception as e:
        print(f"Warning during table drop: {e}")

    print("Creating fresh tables...")

    try:
        # Create all tables with updated schema
        Base.metadata.create_all(bind=engine)
        print("Successfully created all database tables!")

        # List created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")

    except Exception as e:
        print(f"Error creating tables: {e}")
        raise


if __name__ == "__main__":
    recreate_tables()