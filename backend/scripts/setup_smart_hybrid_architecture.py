#!/usr/bin/env python3
"""
Smart Hybrid Architecture Setup Script

This script sets up the complete Smart Hybrid Architecture for the PoE2 crafting system:
1. Creates database tables
2. Populates comprehensive crafting data
3. Validates the system is working

Implements the architecture where:
- Mechanics are in code (stable algorithms)
- Content is in database (flexible configurations)
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.create_tables import create_all_tables
from scripts.populate_comprehensive_crafting_data import main as populate_data
from app.services.crafting.config_service import crafting_config_service
from app.services.crafting.unified_factory import unified_crafting_factory


def validate_system():
    """Validate that the Smart Hybrid Architecture is working correctly."""
    print("\nValidating Smart Hybrid Architecture...")

    try:
        # Test configuration loading
        crafting_config_service.reload_all_configs()

        # Test currency creation
        currencies = unified_crafting_factory.get_all_available_currencies()
        essences = unified_crafting_factory.get_all_available_essences()
        omens = unified_crafting_factory.get_all_available_omens()

        print(f"Loaded {len(currencies)} currencies")
        print(f"Loaded {len(essences)} essences")
        print(f"Loaded {len(omens)} omens")

        # Test creating a currency
        test_currency = unified_crafting_factory.create_currency("Orb of Transmutation")
        if test_currency:
            print("Successfully created test currency")
        else:
            print("Failed to create test currency")
            return False

        # Test creating an essence
        test_essence = unified_crafting_factory.create_currency("Essence of the Body")
        if test_essence:
            print("Successfully created test essence")
        else:
            print("Failed to create test essence")
            return False

        # Test omen lookup
        transmutation_omens = unified_crafting_factory.get_omens_for_currency("Orb of Transmutation")
        print(f"Found {len(transmutation_omens)} omens for Transmutation")

        return True

    except Exception as e:
        print(f"Validation failed: {e}")
        return False


def main():
    """Main setup function."""
    print("Setting up Smart Hybrid Architecture for PoE2 Crafting System")
    print("=" * 70)

    try:
        # Step 1: Create database tables
        print("\nStep 1: Creating database tables...")
        create_all_tables()

        # Step 2: Populate data
        print("\nStep 2: Populating comprehensive crafting data...")
        populate_data()

        # Step 3: Validate system
        print("\nStep 3: Validating system...")
        if validate_system():
            print("\nSUCCESS! Smart Hybrid Architecture is ready!")
            print("\nArchitecture Overview:")
            print("Mechanics (Code):")
            print("   - app/services/crafting/mechanics.py")
            print("   - app/services/crafting/unified_factory.py")
            print("Content (Database):")
            print("   - Currency configurations")
            print("   - Essence data with item-specific effects")
            print("   - Omen rules and interactions")
            print("   - Desecration bones")
            print("   - Modifier pools")
            print("\nUsage:")
            print("   - Mechanics stay stable in code")
            print("   - Content can be updated via database")
            print("   - Easy to balance without code changes")
            print("   - Type-safe and performant")
        else:
            print("\nFAILED! System validation failed")
            return 1

    except Exception as e:
        print(f"\nSETUP FAILED: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)