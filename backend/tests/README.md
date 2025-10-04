# PoE2 AI TradeCraft - Crafting System Test Suite

Comprehensive test suite for the Path of Exile 2 crafting mechanics implementation.

## Overview

This test suite provides extensive coverage of all crafting mechanics, including:

- **Base Currency Mechanics** - Transmutation, Augmentation, Alchemy, Regal, Exalted, Chaos, Divine, Vaal, etc.
- **Essence Mechanics** - All tiers and types of essences
- **Desecration Mechanics** - Abyssal Bones and Well of Souls
- **Omen Mechanics** - All omen types and combinations
- **Modifier Pool** - Filtering, selection, and weighting
- **Unified Factory** - Currency creation and omen application
- **Integration Tests** - End-to-end crafting workflows

## Test Files

### `test_crafting_mechanics.py` (1000+ lines)
Tests for all base currency mechanics:
- ✓ Transmutation (Normal → Magic, 1 mod)
- ✓ Augmentation (Magic 1 mod → Magic 2 mods)
- ✓ Alchemy (Normal → Rare, 4 mods)
- ✓ Regal (Magic → Rare + 1 mod)
- ✓ Exalted (Rare + 1 mod)
- ✓ Chaos (Remove 1, add 1)
- ✓ Divine (Reroll values)
- ✓ Vaal (Corrupt)
- ✓ Annulment (Remove 1)
- ✓ Scouring (Remove all)
- ✓ Omen combinations (Dextral, Sinistral, Greater, Homogenising)
- ✓ Currency variant matching (Perfect, Greater, etc.)
- ✓ Edge cases and error conditions
- ✓ Complete crafting workflows

### `test_essence_mechanics.py` (600+ lines)
Tests for essence crafting:
- ✓ Essence on Normal items (create Magic/Rare)
- ✓ Essence on Magic/Rare items (reroll with guaranteed mod)
- ✓ Essence tiers (Lesser, Greater, Perfect)
- ✓ Essence types (Flames, Ice, Lightning, etc.)
- ✓ Item category restrictions
- ✓ Essence-specific modifiers
- ✓ Corrupted essences
- ✓ Essence + Omen combinations

### `test_desecration_mechanics.py` (700+ lines)
Tests for desecration crafting (Abyssal Bones):
- ✓ Bone tiers (Gnawed, Preserved, Ancient)
- ✓ Bone parts (Jawbone, Rib, Collarbone, Cranium, Finger)
- ✓ Desecrated-only modifier filtering
- ✓ Boss-specific modifiers (Ulaman, Amanamu, Kurgal)
- ✓ Item category restrictions for desecrated mods
- ✓ Bone + Omen combinations
- ✓ Well of Souls mechanics

### `test_modifier_pool.py` (500+ lines)
Tests for modifier pool functionality:
- ✓ Filtering by category
- ✓ Filtering by item level
- ✓ Filtering by tags
- ✓ Filtering by mod groups
- ✓ Desecrated-only filtering
- ✓ Essence-only filtering
- ✓ Excluded group handling
- ✓ Weighted random selection
- ✓ Jewellery category expansion
- ✓ Performance tests

### `test_unified_factory_integration.py` (500+ lines)
Tests for factory and integration:
- ✓ Currency creation from config
- ✓ Omen application and wrapping
- ✓ Essence creation
- ✓ Bone creation
- ✓ Currency variant matching
- ✓ End-to-end crafting workflows
- ✓ Error handling and edge cases

## Running Tests

### Quick Start

```bash
# Run all tests
python tests/run_all_tests.py

# Run with coverage report
python tests/run_all_tests.py --coverage

# Run specific test file
python tests/run_all_tests.py --specific test_crafting_mechanics

# Run with fail-fast (stop on first failure)
python tests/run_all_tests.py --failfast

# List all available test files
python tests/run_all_tests.py --list
```

### Using pytest directly

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_crafting_mechanics.py -v

# Run specific test class
pytest tests/test_crafting_mechanics.py::TestExaltedMechanic -v

# Run specific test method
pytest tests/test_crafting_mechanics.py::TestExaltedMechanic::test_can_apply_to_rare_with_open_slot -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html --cov-report=term-missing

# Run only failed tests from last run
pytest --lf

# Run tests matching a keyword
pytest -k "exalted" -v

# Run with verbose output and stop on first failure
pytest tests/ -vx
```

## Test Structure

Each test file follows a consistent structure:

```python
# ============================================================================
# FIXTURES
# ============================================================================
# Reusable test fixtures for creating test objects

# ============================================================================
# TEST CLASSES
# ============================================================================
# Organized by feature/mechanic being tested

class TestFeatureName:
    """Test description."""

    def test_specific_behavior(self):
        """Should do something specific."""
        # Arrange
        # Act
        # Assert

# ============================================================================
# EDGE CASES AND ERROR CONDITIONS
# ============================================================================
# Tests for edge cases, error handling, and boundary conditions

# ============================================================================
# INTEGRATION TESTS
# ============================================================================
# End-to-end workflow tests
```

## Test Coverage Goals

- **Mechanics Coverage**: 100% of all crafting mechanics
- **Omen Coverage**: All omen types and combinations
- **Edge Cases**: All boundary conditions and error states
- **Integration**: Complete crafting workflows from Normal to 6-mod Rare

## Key Test Scenarios

### Omen Priority Testing
```python
def test_dextral_takes_priority_over_homogenising():
    """
    Critical test: When both Dextral Exaltation and Homogenising Exaltation
    are applied, Dextral should take priority and force suffix addition.

    This test caught the bug where omens weren't being applied at all!
    """
```

### Currency Variant Matching
```python
def test_omen_matches_perfect_exalted():
    """
    Critical test: Omens defined for "Exalted Orb" should also match
    "Perfect Exalted Orb" and "Greater Exalted Orb".

    This test caught the substring matching bug!
    """
```

### Greater Exaltation
```python
def test_greater_exaltation_adds_two_mods():
    """
    Critical test: Omen of Greater Exaltation should add TWO modifiers,
    not one.

    This test caught the unimplemented Greater Exaltation logic!
    """
```

## Common Issues and Solutions

### Import Errors
If you see import errors, make sure you're running from the backend directory:
```bash
cd backend
python -m pytest tests/ -v
```

### Missing Dependencies
Install test dependencies:
```bash
pip install pytest pytest-cov
```

### Database Connection Errors
Some tests may require mocked database connections. Use the provided fixtures.

## Writing New Tests

When adding new crafting mechanics:

1. **Create test fixtures** - Make reusable factories for test objects
2. **Test happy path** - Test the expected behavior
3. **Test edge cases** - Test boundary conditions
4. **Test error handling** - Test failure modes
5. **Test integration** - Test how it works with other mechanics

Example:
```python
class TestNewMechanic:
    """Test NewMechanic currency."""

    def test_can_apply_to_correct_rarity(self, create_test_item):
        """Should be applicable to correct rarity."""
        # Arrange
        item = create_test_item(rarity=ItemRarity.RARE)
        mechanic = NewMechanic({})

        # Act
        can_apply, error = mechanic.can_apply(item)

        # Assert
        assert can_apply is True
        assert error is None

    def test_produces_expected_result(self, create_test_item, mock_modifier_pool):
        """Should produce expected result."""
        # Test implementation
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# .github/workflows/test.yml
- name: Run crafting tests
  run: |
    cd backend
    python tests/run_all_tests.py --coverage --failfast
```

## Performance Benchmarks

The test suite includes performance benchmarks:

- **Modifier pool with 1000 mods**: < 1 second for 100 rolls
- **Complete crafting workflow**: < 100ms
- **Omen application**: < 10ms

## Test Coverage Report

After running with `--coverage`, view the HTML report:

```bash
# Generate coverage report
python tests/run_all_tests.py --coverage

# Open in browser
open htmlcov/index.html  # macOS
start htmlcov/index.html  # Windows
xdg-open htmlcov/index.html  # Linux
```

## Contributing

When contributing new crafting mechanics:

1. Write tests first (TDD approach)
2. Ensure all tests pass
3. Maintain > 90% code coverage
4. Document any new test patterns
5. Add integration tests for complex workflows

## Questions?

If you have questions about the test suite:

1. Check the test file comments
2. Look at similar test patterns
3. Review the fixtures in each file
4. Run specific tests with `-v` for detailed output

---

**Total Test Count**: 100+ test methods covering all crafting mechanics

**Last Updated**: 2025-10-03

**Maintained By**: PoE2 AI TradeCraft Team
