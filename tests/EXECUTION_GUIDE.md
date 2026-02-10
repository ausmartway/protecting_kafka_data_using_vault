# Test Execution Guide

This guide provides step-by-step instructions for running the test suite.

## 📋 Prerequisites Checklist

Before running tests, ensure you have:

- [ ] Python 3.9+ installed
- [ ] Virtual environment created (`.venv`)
- [ ] Project dependencies installed
- [ ] Test dependencies installed

## 🚀 Quick Start

### 1. Install Test Dependencies

```bash
# Activate virtual environment
source .venv/bin/activate

# Install test dependencies
pip install -r requirements-test.txt
```

### 2. Run Unit Tests

```bash
# Using the test runner script
./run_tests.sh unit

# Or using pytest directly
pytest -m unit -v
```

### 3. Run Integration Tests (Optional)

Integration tests require Vault and Kafka to be running:

```bash
# Set environment variables
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="your-token"
export VAULT_NAMESPACE="admin"  # if using namespaces

# Run integration tests
./run_tests.sh integration
```

## 📊 Test Reports

### Generate Coverage Report

```bash
# Generate HTML coverage report
./run_tests.sh coverage

# Or using pytest
pytest --cov=. --cov-report=html --cov-report=term

# Open the report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Generate XML Report (for CI/CD)

```bash
pytest --junitxml=test-results.xml
```

## 🧪 Test Categories

### Unit Tests (`pytest -m unit`)

Fast tests that don't require external services. They use mocks for:
- Vault client
- Kafka producer/consumer
- File system operations

**Typical runtime**: <10 seconds

### Integration Tests (`pytest -m integration`)

Slower tests that require:
- Running Vault instance
- Running Kafka cluster
- Valid configuration

**Typical runtime**: 30-60 seconds

## 🔧 Troubleshooting

### Issue: Import Errors

```bash
# Solution: Install dependencies
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### Issue: Module Not Found

```bash
# Solution: Ensure you're in the project root
pwd  # Should show .../protecting_kafka_data_using_vault
```

### Issue: Vault/Kafka Connection Failed (Integration Tests)

```bash
# Solution: Check services are running
curl $VAULT_ADDR/v1/sys/health

# Or skip integration tests
pytest -m "not integration"
```

### Issue: Timeout Errors

```bash
# Solution: Increase timeout
pytest --timeout=60

# Or run fast tests only
pytest -m unit -m "not slow"
```

## 📈 CI/CD Integration

### GitHub Actions

```yaml
- name: Run tests
  run: |
    pip install -r requirements-test.txt
    pytest -m unit -v
```

### GitLab CI

```yaml
test:
  script:
    - pip install -r requirements-test.txt
    - pytest -m unit -v
```

## 🎯 Best Practices

1. **Run unit tests frequently** during development
2. **Run integration tests** before committing
3. **Check coverage** before pushing to remote
4. **Fix failing tests** immediately
5. **Add tests** for new features

## 📞 Getting Help

If you encounter issues:

1. Check the [README.md](README.md) for project setup
2. Review test output for specific error messages
3. Ensure all dependencies are installed
4. Verify environment variables (for integration tests)

## 🔄 Continuous Testing

For a better development workflow, consider using:

```bash
# Install pytest-watch for continuous testing
pip install pytest-watch

# Run tests automatically when files change
ptw -p 'pytest -m unit -v'
```
