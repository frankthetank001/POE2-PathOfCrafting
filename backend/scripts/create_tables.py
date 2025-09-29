#!/usr/bin/env python3
"""
Create Database Tables - Smart Hybrid Architecture

Creates all database tables for the comprehensive crafting system.
Run this before populating data.
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


def create_all_tables():
    """Create all database tables."""
    print("Creating database tables...")

    try:
        # Create all tables
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
    create_all_tables()