#!/bin/bash
# Test runner script for Kafka Vault encryption project

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Kafka Vault Encryption - Test Runner${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -q -r requirements.txt
pip install -q -r requirements-test.txt

# Run tests based on arguments
TEST_TYPE="${1:-unit}"

case $TEST_TYPE in
    unit)
        echo -e "${GREEN}Running unit tests...${NC}"
        pytest -m unit -v
        ;;
    integration)
        echo -e "${GREEN}Running integration tests...${NC}"
        echo -e "${YELLOW}Note: Integration tests require Vault and Kafka to be running${NC}"
        pytest -m integration -v
        ;;
    all)
        echo -e "${GREEN}Running all tests...${NC}"
        pytest -v
        ;;
    coverage)
        echo -e "${GREEN}Running tests with coverage...${NC}"
        pytest --cov=. --cov-report=html --cov-report=term
        echo -e "${GREEN}Coverage report generated in htmlcov/${NC}"
        ;;
    fast)
        echo -e "${GREEN}Running fast unit tests only...${NC}"
        pytest -m unit -v --timeout=10
        ;;
    *)
        echo -e "${RED}Unknown test type: $TEST_TYPE${NC}"
        echo "Usage: $0 [unit|integration|all|coverage|fast]"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Tests completed!${NC}"
echo -e "${GREEN}========================================${NC}"
