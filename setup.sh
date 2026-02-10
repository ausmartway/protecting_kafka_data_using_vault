#!/bin/bash

set -e

echo "🚀 Setting up Local Kafka + Vault Demo Environment"
echo "=================================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "   Please edit .env file with your Vault license path if using Enterprise"
    echo ""
fi

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set default namespace if not set (required by Python scripts)
if [ -z "$VAULT_NAMESPACE" ]; then
    export VAULT_NAMESPACE=""
    echo "ℹ️  VAULT_NAMESPACE not set, using empty namespace (Vault OSS)"
fi

# Check if Docker is running
echo "🐳 Checking Docker..."
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi
echo "✅ Docker is running!"
echo ""

# Check if Docker Compose is available
echo "🔧 Checking Docker Compose..."
if ! docker compose version > /dev/null 2>&1; then
    echo "❌ Docker Compose is not available. Please install Docker Compose v2."
    exit 1
fi
echo "✅ Docker Compose is available!"
echo ""

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p source
mkdir -p destination
echo "✅ Directories created!"
echo ""

# Start services
echo "🚀 Starting Docker Compose services..."
docker compose up -d
echo "✅ Services started!"
echo ""

# Wait for Kafka to be healthy
echo "⏳ Waiting for Kafka to be healthy..."
timeout=60
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null; then
        echo "✅ Kafka is healthy!"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo "   Waiting... ($elapsed/$timeout seconds)"
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ Timeout waiting for Kafka to be healthy"
    exit 1
fi
echo ""

# Wait for Vault to be healthy
echo "⏳ Waiting for Vault to be healthy..."
timeout=30
elapsed=0
while [ $elapsed -lt $timeout ]; do
    if docker exec vault vault status > /dev/null 2>&1; then
        echo "✅ Vault is healthy!"
        break
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    echo "   Waiting... ($elapsed/$timeout seconds)"
done

if [ $elapsed -ge $timeout ]; then
    echo "❌ Timeout waiting for Vault to be healthy"
    exit 1
fi
echo ""

# Create Kafka topics
echo "📚 Creating Kafka topics..."
./scripts/create-topics.sh
echo ""

# Initialize Vault
echo "🔐 Initializing Vault..."
./scripts/init-vault.sh
echo ""

# Setup Kafka configuration
echo "⚙️  Setting up Kafka configuration..."
if [ ! -f getting_started.ini ]; then
    cp getting_started.local.ini getting_started.ini
    echo "✅ Created getting_started.ini from local template"
else
    echo "⚠️  getting_started.ini already exists, skipping..."
fi
echo ""

echo "✨ Setup complete!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎉 Your local Kafka + Vault demo environment is ready!"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📍 Service URLs:"
echo "   Kafka:          localhost:9092"
echo "   Vault:          http://localhost:8200"
echo "   Kafka UI:       http://localhost:8080"
echo ""
echo "🔑 Environment Variables (already set):"
echo "   VAULT_ADDR=$VAULT_ADDR"
echo "   VAULT_TOKEN=$VAULT_TOKEN"
if [ -n "$VAULT_NAMESPACE" ]; then
    echo "   VAULT_NAMESPACE=$VAULT_NAMESPACE"
fi
echo ""
echo "📚 Demo Scripts:"
echo "   1. Produce plaintext messages:"
echo "      python3 producer.py"
echo ""
echo "   2. Encrypt and consume (in separate terminals):"
echo "      python3 encryptor.py"
echo "      python3 consumer_from_encrypted.py"
echo ""
echo "   3. Large file transfer (in separate terminals):"
echo "      # Copy files to source/ directory first"
echo "      python3 producer_file_transfer.py"
echo "      python3 consumer_file_transfer.py"
echo ""
echo "🛑 To stop the demo:"
echo "   ./teardown.sh"
echo ""
echo "📖 For more information, see README.md"
echo ""
