#!/usr/bin/env python3
"""
Test validation script to verify test structure without running pytest.
This script validates that test files are properly structured.
"""

import os
import sys
from pathlib import Path

# Change to project root directory
script_dir = Path(__file__).parent
os.chdir(script_dir.parent)


def check_test_structure():
    """Check that test directory structure is correct."""
    print("Checking test directory structure...")

    required_dirs = [
        'tests',
        'tests/unit',
        'tests/integration',
        'tests/fixtures'
    ]

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {dir_path} exists")
        else:
            print(f"✗ {dir_path} missing")
            return False

    return True


def check_test_files():
    """Check that required test files exist."""
    print("\nChecking test files...")

    required_files = [
        'tests/__init__.py',
        'tests/conftest.py',
        'tests/unit/__init__.py',
        'tests/unit/test_producer.py',
        'tests/unit/test_consumer.py',
        'tests/unit/test_encryptor.py',
        'tests/unit/test_consumer_from_encrypted.py',
        'tests/unit/test_producer_file_transfer.py',
        'tests/unit/test_consumer_file_transfer.py',
        'tests/integration/__init__.py',
        'tests/integration/test_integration.py',
    ]

    all_exist = True
    for file_path in required_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            all_exist = False

    return all_exist


def count_test_cases():
    """Count test cases in test files."""
    print("\nCounting test cases...")

    test_files = list(Path('tests/unit').glob('test_*.py')) + \
                 list(Path('tests/integration').glob('test_*.py'))

    total_tests = 0
    for test_file in test_files:
        with open(test_file, 'r') as f:
            content = f.read()
            test_count = content.count('def test_')
            total_tests += test_count
            print(f"  {test_file.name}: {test_count} tests")

    print(f"\nTotal: {total_tests} test cases")
    return total_tests


def check_configuration_files():
    """Check that configuration files exist."""
    print("\nChecking configuration files...")

    config_files = [
        'pytest.ini',
        'requirements-test.txt',
        'run_tests.sh'
    ]

    all_exist = True
    for file_path in config_files:
        path = Path(file_path)
        if path.exists():
            print(f"✓ {file_path} exists")
        else:
            print(f"✗ {file_path} missing")
            all_exist = False

    return all_exist


def main():
    """Main validation function."""
    print("=" * 60)
    print("Test Suite Validation")
    print("=" * 60)

    structure_ok = check_test_structure()
    files_ok = check_test_files()
    config_ok = check_configuration_files()
    test_count = count_test_cases()

    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)

    if structure_ok and files_ok and config_ok:
        print("✓ All test files and structure validated successfully!")
        print(f"✓ Total test cases: {test_count}")
        print("\nTo run tests:")
        print("  1. Install dependencies: pip install -r requirements-test.txt")
        print("  2. Run unit tests: pytest -m unit -v")
        print("  3. Run all tests: pytest -v")
        print("  4. Or use: ./run_tests.sh unit")
        return 0
    else:
        print("✗ Some issues found. Please review the output above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
