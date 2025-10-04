"""
Pytest configuration and shared fixtures for the test suite.

This file contains:
- Shared fixtures used across multiple test files
- Pytest configuration hooks
- Common test utilities
"""

import pytest
import sys
from pathlib import Path
from typing import List

# Add backend directory to path for imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.schemas.crafting import (
    CraftableItem,
    ItemModifier,
    ItemRarity,
    ModType,
    OmenInfo,
    OmenRule,
)


# ============================================================================
# SHARED FIXTURES
# ============================================================================

@pytest.fixture
def create_test_modifier():
    """
    Shared fixture for creating test modifiers.

    Usage:
        def test_something(create_test_modifier):
            mod = create_test_modifier("Test Mod", ModType.PREFIX)
            assert mod.name == "Test Mod"
    """
    def _create(
        name: str,
        mod_type: ModType,
        tier: int = 1,
        stat_min: int = 10,
        stat_max: int = 20,
        required_ilvl: int = 1,
        applicable_items: List[str] = None,
        tags: List[str] = None,
        mod_group: str = None,
        weight: int = 100,
        is_essence_only: bool = False,
        is_exclusive: bool = False,
    ):
        return ItemModifier(
            name=name,
            mod_type=mod_type,
            tier=tier,
            stat_text=f"{name} stat text",
            stat_min=stat_min,
            stat_max=stat_max,
            required_ilvl=required_ilvl,
            weight=weight,
            mod_group=mod_group or f"{name}_group",
            applicable_items=applicable_items or ["body_armour", "int_armour"],
            tags=tags or [],
            is_essence_only=is_essence_only,
            is_exclusive=is_exclusive,
        )
    return _create


@pytest.fixture
def create_test_item():
    """
    Shared fixture for creating test items.

    Usage:
        def test_something(create_test_item):
            item = create_test_item(rarity=ItemRarity.RARE)
            assert item.rarity == ItemRarity.RARE
    """
    def _create(
        rarity: ItemRarity = ItemRarity.NORMAL,
        item_level: int = 80,
        base_name: str = "Vile Robe",
        base_category: str = "int_armour",
        prefix_mods: List[ItemModifier] = None,
        suffix_mods: List[ItemModifier] = None,
        corrupted: bool = False,
        quality: int = 20,
    ):
        return CraftableItem(
            base_name=base_name,
            base_category=base_category,
            rarity=rarity,
            item_level=item_level,
            quality=quality,
            prefix_mods=prefix_mods or [],
            suffix_mods=suffix_mods or [],
            corrupted=corrupted,
        )
    return _create


@pytest.fixture
def create_omen_info():
    """
    Shared fixture for creating omen info objects.

    Usage:
        def test_something(create_omen_info):
            omen = create_omen_info(
                name="Omen of Dextral Exaltation",
                affected_currency="Exalted Orb",
                effect_type="dextral"
            )
            assert omen.effect_type == "dextral"
    """
    def _create(
        name: str = "Test Omen",
        effect_description: str = "Test effect",
        affected_currency: str = "Chaos Orb",
        effect_type: str = "test",  # Required field
        stack_size: int = 10,
        rules: List[OmenRule] = None,
        omen_id: int = 1,
    ):
        return OmenInfo(
            id=omen_id,
            name=name,
            effect_description=effect_description,
            affected_currency=affected_currency,
            effect_type=effect_type,
            stack_size=stack_size,
            rules=rules or [],
        )
    return _create


@pytest.fixture
def sample_prefix_mods(create_test_modifier):
    """
    Fixture providing sample prefix modifiers.

    Usage:
        def test_something(sample_prefix_mods):
            mods = sample_prefix_mods(count=3)
            assert len(mods) == 3
    """
    def _create(count: int = 1):
        return [
            create_test_modifier(f"Prefix{i}", ModType.PREFIX)
            for i in range(count)
        ]
    return _create


@pytest.fixture
def sample_suffix_mods(create_test_modifier):
    """
    Fixture providing sample suffix modifiers.

    Usage:
        def test_something(sample_suffix_mods):
            mods = sample_suffix_mods(count=3)
            assert len(mods) == 3
    """
    def _create(count: int = 1):
        return [
            create_test_modifier(f"Suffix{i}", ModType.SUFFIX)
            for i in range(count)
        ]
    return _create


@pytest.fixture
def normal_item(create_test_item):
    """Fixture providing a Normal rarity item."""
    return create_test_item(rarity=ItemRarity.NORMAL)


@pytest.fixture
def magic_item(create_test_item, create_test_modifier):
    """Fixture providing a Magic rarity item with 1 prefix."""
    prefix = create_test_modifier("Magic Prefix", ModType.PREFIX)
    return create_test_item(rarity=ItemRarity.MAGIC, prefix_mods=[prefix])


@pytest.fixture
def rare_item(create_test_item, sample_prefix_mods, sample_suffix_mods):
    """Fixture providing a Rare rarity item with 2 prefixes and 2 suffixes."""
    prefixes = sample_prefix_mods(count=2)
    suffixes = sample_suffix_mods(count=2)
    return create_test_item(
        rarity=ItemRarity.RARE,
        prefix_mods=prefixes,
        suffix_mods=suffixes,
    )


@pytest.fixture
def full_rare_item(create_test_item, sample_prefix_mods, sample_suffix_mods):
    """Fixture providing a Rare item with 6 modifiers (3 prefix, 3 suffix)."""
    prefixes = sample_prefix_mods(count=3)
    suffixes = sample_suffix_mods(count=3)
    return create_test_item(
        rarity=ItemRarity.RARE,
        prefix_mods=prefixes,
        suffix_mods=suffixes,
    )


# ============================================================================
# PYTEST CONFIGURATION HOOKS
# ============================================================================

def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "essence: marks tests related to essence mechanics"
    )
    config.addinivalue_line(
        "markers", "desecration: marks tests related to desecration mechanics"
    )
    config.addinivalue_line(
        "markers", "omen: marks tests related to omen mechanics"
    )


def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to add markers automatically.

    This hook automatically marks tests based on their location/name.
    """
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)

        # Mark essence tests
        if "essence" in item.nodeid.lower():
            item.add_marker(pytest.mark.essence)

        # Mark desecration tests
        if "desecration" in item.nodeid.lower():
            item.add_marker(pytest.mark.desecration)

        # Mark omen tests
        if "omen" in item.nodeid.lower():
            item.add_marker(pytest.mark.omen)


# ============================================================================
# TEST UTILITIES
# ============================================================================

class TestHelpers:
    """Helper utilities for tests."""

    @staticmethod
    def assert_item_has_mods(item: CraftableItem, expected_count: int):
        """Assert that an item has the expected number of modifiers."""
        actual = item.total_explicit_mods
        assert actual == expected_count, (
            f"Expected {expected_count} mods, got {actual}. "
            f"Prefixes: {item.prefix_count}, Suffixes: {item.suffix_count}"
        )

    @staticmethod
    def assert_mod_type_count(item: CraftableItem, mod_type: str, expected: int):
        """Assert that an item has the expected count of a specific mod type."""
        if mod_type == "prefix":
            actual = item.prefix_count
        elif mod_type == "suffix":
            actual = item.suffix_count
        else:
            raise ValueError(f"Invalid mod_type: {mod_type}")

        assert actual == expected, (
            f"Expected {expected} {mod_type}es, got {actual}"
        )

    @staticmethod
    def assert_rarity_upgraded(
        original: ItemRarity,
        result: ItemRarity,
        expected: ItemRarity
    ):
        """Assert that rarity was upgraded correctly."""
        assert result == expected, (
            f"Expected rarity upgrade from {original.value} to {expected.value}, "
            f"got {result.value}"
        )


@pytest.fixture
def test_helpers():
    """Fixture providing test helper utilities."""
    return TestHelpers


# ============================================================================
# PERFORMANCE MONITORING
# ============================================================================

@pytest.fixture
def timer():
    """
    Fixture for timing test execution.

    Usage:
        def test_something(timer):
            with timer("operation name"):
                # do something
            # Automatically asserts operation took < 1 second
    """
    import time
    from contextlib import contextmanager

    @contextmanager
    def _timer(name: str, max_seconds: float = 1.0):
        start = time.time()
        yield
        elapsed = time.time() - start
        assert elapsed < max_seconds, (
            f"{name} took {elapsed:.3f}s, expected < {max_seconds}s"
        )

    return _timer


# ============================================================================
# SNAPSHOT TESTING (Optional)
# ============================================================================

@pytest.fixture
def snapshot_item():
    """
    Create a snapshot of an item for comparison testing.

    Usage:
        def test_something(snapshot_item):
            item = create_item()
            snapshot = snapshot_item(item)
            # ... modify item ...
            assert snapshot != snapshot_item(item)
    """
    def _snapshot(item: CraftableItem) -> dict:
        return {
            "rarity": item.rarity.value,
            "prefix_count": item.prefix_count,
            "suffix_count": item.suffix_count,
            "total_mods": item.total_explicit_mods,
            "corrupted": item.corrupted,
            "quality": item.quality,
        }
    return _snapshot


# ============================================================================
# DEBUGGING HELPERS
# ============================================================================

@pytest.fixture
def debug_item():
    """
    Print detailed information about an item for debugging.

    Usage:
        def test_something(debug_item):
            item = create_item()
            debug_item(item)  # Prints detailed item info
    """
    def _debug(item: CraftableItem):
        print("\n" + "=" * 60)
        print(f"Item: {item.base_name} ({item.base_category})")
        print(f"Rarity: {item.rarity.value}")
        print(f"Item Level: {item.item_level}")
        print(f"Quality: {item.quality}%")
        print(f"Corrupted: {item.corrupted}")
        print(f"\nPrefixes ({item.prefix_count}):")
        for i, mod in enumerate(item.prefix_mods, 1):
            print(f"  {i}. {mod.name} (tier {mod.tier}, ilvl {mod.required_ilvl})")
        print(f"\nSuffixes ({item.suffix_count}):")
        for i, mod in enumerate(item.suffix_mods, 1):
            print(f"  {i}. {mod.name} (tier {mod.tier}, ilvl {mod.required_ilvl})")
        print("=" * 60 + "\n")
    return _debug
