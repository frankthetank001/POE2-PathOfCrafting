#!/usr/bin/env python3
"""Test script to verify hybrid modifier rolling."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from contextlib import contextmanager
from app.models.base import SessionLocal

@contextmanager
def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
from app.models.crafting import Modifier
from app.services.crafting.modifier_loader import ModifierLoader
from app.services.crafting.modifier_pool import ModifierPool
from app.schemas.crafting import CraftableItem, ItemRarity

def test_hybrid_mod_in_database():
    """Check if Divine modifier has correct stat_ranges in database."""
    print("=" * 60)
    print("TEST 1: Check Divine modifier in database")
    print("=" * 60)

    with get_db_session() as db:
        # Find the Divine modifier (hybrid ES mod)
        divine_mod = db.query(Modifier).filter(
            Modifier.name.ilike("%Divine%"),
            Modifier.stat_text.ilike("%Energy Shield%")
        ).first()

        if divine_mod:
            print(f"Found: {divine_mod.name}")
            print(f"Stat Text: {divine_mod.stat_text}")
            print(f"Stat Ranges: {divine_mod.stat_ranges}")
            print(f"Stat Min: {divine_mod.stat_min}")
            print(f"Stat Max: {divine_mod.stat_max}")
            print(f"Type: stat_ranges = {type(divine_mod.stat_ranges)}")

            if divine_mod.stat_ranges:
                print(f"\nNumber of ranges: {len(divine_mod.stat_ranges)}")
                for i, r in enumerate(divine_mod.stat_ranges):
                    print(f"  Range {i}: {r}")
            else:
                print("\n⚠️  WARNING: stat_ranges is empty!")

            return divine_mod
        else:
            print("❌ Divine modifier not found!")
            return None


def test_modifier_loader():
    """Check if ModifierLoader correctly loads stat_ranges."""
    print("\n" + "=" * 60)
    print("TEST 2: Check ModifierLoader parsing")
    print("=" * 60)

    # Force reload
    ModifierLoader.reload_modifiers()

    # Get all modifiers
    all_mods = ModifierLoader.get_modifiers()

    # Find Divine modifier
    divine_mods = [m for m in all_mods if "Divine" in m.name and "Energy Shield" in m.stat_text]

    if divine_mods:
        for mod in divine_mods[:3]:  # Show first 3
            print(f"\nModifier: {mod.name}")
            print(f"Stat Text: {mod.stat_text}")
            print(f"Stat Ranges: {mod.stat_ranges}")
            print(f"Type: {type(mod.stat_ranges)}")

            if mod.stat_ranges:
                print(f"Number of ranges: {len(mod.stat_ranges)}")
                for i, r in enumerate(mod.stat_ranges):
                    print(f"  Range {i}: min={r.min}, max={r.max}")
            else:
                print("⚠️  WARNING: stat_ranges is empty!")
    else:
        print("❌ No Divine modifiers found in loader!")

    return divine_mods[0] if divine_mods else None


def test_modifier_pool_rolling():
    """Test if ModifierPool correctly rolls current_values."""
    print("\n" + "=" * 60)
    print("TEST 3: Check ModifierPool rolling")
    print("=" * 60)

    # Load modifiers
    all_mods = ModifierLoader.get_modifiers()
    pool = ModifierPool(all_mods)

    # Create a test item
    test_item = CraftableItem(
        base_name="Vile Robe",
        base_category="int_armour",
        rarity=ItemRarity.NORMAL,
        item_level=82,
        quality=20
    )

    # Try to roll a prefix modifier multiple times
    print("\nRolling 5 random prefixes for int_armour:")
    for i in range(5):
        rolled_mod = pool.roll_random_modifier(
            mod_type="prefix",
            item_category="int_armour",
            item_level=82,
            item=test_item
        )

        if rolled_mod:
            print(f"\n  Roll {i+1}: {rolled_mod.name}")
            print(f"    Stat Text: {rolled_mod.stat_text}")
            print(f"    Has stat_ranges: {rolled_mod.stat_ranges is not None and len(rolled_mod.stat_ranges) > 0}")
            print(f"    current_value: {rolled_mod.current_value}")
            print(f"    current_values: {rolled_mod.current_values}")

            if rolled_mod.stat_ranges and len(rolled_mod.stat_ranges) > 1:
                print(f"    [HYBRID] HYBRID MOD DETECTED!")
                print(f"    Stat Ranges: {[(r.min, r.max) for r in rolled_mod.stat_ranges]}")

                if rolled_mod.current_values and len(rolled_mod.current_values) > 1:
                    print(f"    [OK] Multiple values rolled: {rolled_mod.current_values}")
                else:
                    print(f"    [ERROR] Hybrid mod but only one value!")


def test_divine_orb_simulation():
    """Test a full Divine Orb simulation via API."""
    print("\n" + "=" * 60)
    print("TEST 4: Simulate Divine Orb via crafting mechanics")
    print("=" * 60)

    from app.services.crafting.mechanics import AlchemyMechanic, DivineMechanic
    from app.services.crafting.modifier_loader import ModifierLoader
    from app.services.crafting.modifier_pool import ModifierPool

    # Create test item
    test_item = CraftableItem(
        base_name="Vile Robe",
        base_category="int_armour",
        rarity=ItemRarity.NORMAL,
        item_level=82,
        quality=20
    )

    # Load modifiers
    all_mods = ModifierLoader.get_modifiers()
    pool = ModifierPool(all_mods)

    # Apply Alchemy to make it rare
    print("\nApplying Orb of Alchemy...")
    from app.models.crafting import CurrencyConfig
    alchemy_config = {"name": "Orb of Alchemy"}
    alchemy = AlchemyMechanic(config=alchemy_config)
    success, msg, test_item = alchemy.apply(test_item, pool)
    print(f"  Result: {msg}")

    # Show the modifiers
    print(f"\nItem now has {len(test_item.prefix_mods)} prefixes:")
    for mod in test_item.prefix_mods:
        print(f"  - {mod.name}: {mod.stat_text}")
        print(f"    stat_ranges: {mod.stat_ranges}")
        print(f"    current_values: {mod.current_values}")
        if mod.stat_ranges and len(mod.stat_ranges) > 1:
            print(f"    [HYBRID MOD]")

    # Apply Divine Orb
    print("\nApplying Divine Orb...")
    divine_config = {"name": "Divine Orb"}
    divine = DivineMechanic(config=divine_config)
    success, msg, test_item = divine.apply(test_item, pool)
    print(f"  Result: {msg}")

    # Show the rerolled modifiers
    print(f"\nAfter Divine, prefixes:")
    for mod in test_item.prefix_mods:
        print(f"  - {mod.name}: {mod.stat_text}")
        print(f"    current_values: {mod.current_values}")
        if mod.stat_ranges and len(mod.stat_ranges) > 1:
            if mod.current_values and len(mod.current_values) > 1:
                print(f"    [OK] Hybrid values rerolled: {mod.current_values}")
            else:
                print(f"    [ERROR] Hybrid mod but only one value after Divine!")


if __name__ == "__main__":
    print("\nHYBRID MODIFIER TESTING SUITE")
    print("=" * 60)

    # Run all tests
    test_hybrid_mod_in_database()
    test_modifier_loader()
    test_modifier_pool_rolling()
    test_divine_orb_simulation()

    print("\n" + "=" * 60)
    print("ALL TESTS COMPLETED")
    print("=" * 60)
