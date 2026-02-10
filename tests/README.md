# Test Suite for Kafka Vault Encryption Project

This directory contains comprehensive test cases for the Kafka Vault encryption project.

## 📋 Table of Contents

- [Test Structure](#test-structure)
- [Prerequisites](#prerequisites)
- [Running Tests](#running-tests)
- [Test Coverage](#test-coverage)
- [Writing New Tests](#writing-new-tests)
- [CI/CD Integration](#cicd-integration)

## 📁 Test Structure

```
tests/
├── conftest.py                 # Shared fixtures and configuration
├── unit/                       # Unit tests (no external dependencies)
│   ├── test_producer.py
│   ├── test_consumer.py
│   ├── test_encryptor.py
│   ├── test_consumer_from_encrypted.py
│   ├── test_producer_file_transfer.py
│   └── test_consumer_file_transfer.py
└── integration/                # Integration tests (require Vault & Kafka)
    └── test_integration.py
```

## 📦 Prerequisites

### For Unit Tests

```bash
# Install test dependencies
pip install -r requirements-test.txt
```

### For Integration Tests

Integration tests require:
- **Vault Enterprise** with Transit and Transform secrets engines configured
- **Kafka/Confluent cluster** running and accessible
- Valid `getting_started.ini` configuration file
- Environment variables set:
  - `VAULT_ADDR`
  - `VAULT_TOKEN`
  - `VAULT_NAMESPACE` (if using namespaces)

## 🚀 Running Tests

### Quick Start

```bash
# Run all unit tests
./run_tests.sh unit

# Run all tests (unit + integration)
./run_tests.sh all

# Run with coverage report
./run_tests.sh coverage

# Run fast tests only
./run_tests.sh fast
```

### Using pytest Directly

```bash
# Run all unit tests
pytest -m unit -v

# Run all integration tests
pytest -m integration -v

# Run specific test file
pytest tests/unit/test_producer.py -v

# Run specific test class
pytest tests/unit/test_producer.py::TestProducerConfiguration -v

# Run specific test
pytest tests/unit/test_producer.py::TestProducerConfiguration::test_producer_initialization -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -vv

# Run and stop on first failure
pytest -x
```

### Test Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only Vault-related tests
pytest -m vault

# Run only Kafka-related tests
pytest -m kafka

# Run tests NOT marked as slow
pytest -m "not slow"
```

## 📊 Test Coverage

### Unit Tests

Unit tests cover the following areas:

#### Producer Tests (`test_producer.py`)
- Configuration and initialization
- Message generation logic
- Credit card format validation
- Data types and validation
- Kafka interaction
- Message count configuration

#### Consumer Tests (`test_consumer.py`)
- Configuration and initialization
- Message handling
- Offset reset functionality
- Topic subscription
- Polling mechanisms
- Output formatting
- Graceful shutdown

#### Encryptor Tests (`test_encryptor.py`)
- Vault integration
- Transform secrets engine (credit cards)
- Transit secrets engine (addresses)
- Payload transformation
- Base64 encoding/decoding
- Kafka producer/consumer interaction
- TLS verification settings

#### Decryption Consumer Tests (`test_consumer_from_encrypted.py`)
- Configuration
- Transform decryption
- Transit decryption
- Payload reconstruction
- Vault integration
- Output formatting

#### File Transfer Producer Tests (`test_producer_file_transfer.py`)
- Configuration
- File reading operations
- Vault integration (DEK generation)
- AES encryption
- HTTP headers for encrypted data
- Envelope encryption
- Message size handling

#### File Transfer Consumer Tests (`test_consumer_file_transfer.py`)
- Configuration
- Message processing
- DEK decryption
- AES decryption
- File writing operations
- Encrypted payload parsing

### Integration Tests

Integration tests cover:
- Vault connection and authentication
- Transit secrets engine operations
- Transform secrets engine operations
- Kafka producer/consumer operations
- End-to-end encryption flow
- Envelope encryption flow
- Configuration file validation

## ✍️ Writing New Tests

### Unit Test Template

```python
"""
Tests for <module_name>.py
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.unit
class TestFeatureName:
    """Test feature description."""

    def test_specific_behavior(self):
        """Test that specific behavior works correctly."""
        # Arrange
        expected_value = "expected"

        # Act
        actual_value = "actual"

        # Assert
        assert actual_value == expected_value
```

### Integration Test Template

```python
"""
Integration tests for <feature>.
"""

import pytest
from unittest.mock import Mock

@pytest.mark.integration
class TestFeatureIntegration:
    """Test feature integration with external services."""

    @pytest.fixture(autouse=True)
    def setup(self, vault_env_vars):
        """Setup test environment."""
        # Setup code here
        yield
        # Cleanup code here

    def test_integration_scenario(self):
        """Test integration scenario."""
        # Test code here
        pass
```

### Using Fixtures

Available fixtures in `conftest.py`:

- `vault_env_vars` - Vault environment variables
- `sample_pci_data` - Sample PII/PCI data
- `mock_vault_client` - Mocked Vault client
- `mock_kafka_producer` - Mocked Kafka producer
- `mock_kafka_consumer` - Mocked Kafka consumer
- `temp_config_file` - Temporary configuration file
- `temp_source_dir` - Temporary source directory with test files
- `temp_dest_dir` - Temporary destination directory

Example usage:

```python
def test_with_fixtures(mock_vault_client, sample_pci_data):
    """Test using fixtures."""
    # Use mock_vault_client to test Vault operations
    response = mock_vault_client.secrets.transit.encrypt_data(...)
    assert 'ciphertext' in response['data']

    # Use sample_pci_data for testing
    assert 'credit_card' in sample_pci_data
```

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest -m unit -v

      - name: Run coverage
        run: pytest --cov=. --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 📈 Test Goals

- **Unit Tests**: Aim for >80% code coverage
- **Integration Tests**: Cover critical end-to-end flows
- **Speed**: Unit tests should complete in <10 seconds
- **Reliability**: Tests should be deterministic and repeatable

## 🛠️ Troubleshooting

### Import Errors

If you encounter import errors:
```bash
# Ensure you're in the project root directory
cd /path/to/project

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Vault Connection Issues

For integration tests:
```bash
# Check Vault is accessible
curl $VAULT_ADDR/v1/sys/health

# Check token is valid
vault status
```

### Kafka Connection Issues

For integration tests:
```bash
# Check Kafka configuration
cat getting_started.ini

# Test connection with producer/consumer scripts
python3 producer.py
python3 consumer.py
```

## 📝 Best Practices

1. **Keep tests independent** - Each test should be able to run in isolation
2. **Use descriptive names** - Test names should clearly describe what they test
3. **Arrange-Act-Assert** - Structure tests clearly with setup, execution, and verification
4. **Mock external dependencies** - Unit tests should not require external services
5. **Use fixtures** - Share common setup code through fixtures
6. **Test edge cases** - Include tests for error conditions and boundary cases
7. **Keep tests fast** - Unit tests should be quick to run
8. **Review coverage** - Regularly check test coverage reports

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [Vault Documentation](https://developer.hashicorp.com/vault/docs)
- [Confluent Kafka Python Documentation](https://docs.confluent.io/platform/current/clients/python.html)
- [Project README](../README.MD)
