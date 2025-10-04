"""
Test Runner for PoE2 AI TradeCraft Crafting System

Runs all comprehensive test suites and generates coverage reports.

Usage:
    python tests/run_all_tests.py              # Run all tests
    python tests/run_all_tests.py --verbose    # Run with verbose output
    python tests/run_all_tests.py --coverage   # Run with coverage report
    python tests/run_all_tests.py --specific test_crafting_mechanics  # Run specific test file
"""

import sys
import pytest
import argparse
from pathlib import Path


def run_tests(args):
    """Run the test suite based on provided arguments."""

    # Base pytest arguments
    pytest_args = []

    # Add verbosity
    if args.verbose:
        pytest_args.append("-v")
    else:
        pytest_args.append("-v")  # Always use verbose by default

    # Add coverage
    if args.coverage:
        pytest_args.extend([
            "--cov=app",
            "--cov-report=html",
            "--cov-report=term-missing",
        ])

    # Add specific test file if provided
    if args.specific:
        test_file = Path(__file__).parent / f"{args.specific}.py"
        if not test_file.exists():
            print(f"Error: Test file {test_file} not found")
            sys.exit(1)
        pytest_args.append(str(test_file))
    else:
        # Run all tests in tests directory
        pytest_args.append(str(Path(__file__).parent))

    # Add markers if specified
    if args.markers:
        pytest_args.extend(["-m", args.markers])

    # Add fail fast if specified
    if args.failfast:
        pytest_args.append("-x")

    # Add output options
    pytest_args.extend([
        "--tb=short",  # Shorter traceback format
        "--color=yes",  # Colored output
    ])

    # Print test configuration
    print("=" * 80)
    print("PoE2 AI TradeCraft - Crafting System Test Suite")
    print("=" * 80)
    print(f"Running tests with args: {' '.join(pytest_args)}")
    print("=" * 80)
    print()

    # Run pytest
    exit_code = pytest.main(pytest_args)

    # Print summary
    print()
    print("=" * 80)
    if exit_code == 0:
        print("✓ All tests passed!")
    else:
        print(f"✗ Tests failed with exit code {exit_code}")

    if args.coverage:
        print()
        print("Coverage report generated in htmlcov/index.html")

    print("=" * 80)

    return exit_code


def main():
    """Parse arguments and run tests."""
    parser = argparse.ArgumentParser(
        description="Run PoE2 AI TradeCraft crafting system tests"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )

    parser.add_argument(
        "-c", "--coverage",
        action="store_true",
        help="Generate coverage report"
    )

    parser.add_argument(
        "-s", "--specific",
        type=str,
        help="Run specific test file (e.g., test_crafting_mechanics)"
    )

    parser.add_argument(
        "-m", "--markers",
        type=str,
        help="Run tests matching given mark expression (e.g., 'slow' or 'not slow')"
    )

    parser.add_argument(
        "-x", "--failfast",
        action="store_true",
        help="Stop on first test failure"
    )

    parser.add_argument(
        "--list",
        action="store_true",
        help="List all available test files"
    )

    args = parser.parse_args()

    # List available tests if requested
    if args.list:
        print("Available test files:")
        test_files = sorted(Path(__file__).parent.glob("test_*.py"))
        for test_file in test_files:
            print(f"  - {test_file.stem}")
        return 0

    # Run tests
    return run_tests(args)


if __name__ == "__main__":
    sys.exit(main())
