#!/bin/bash

set -e

echo "🛑 Tearing Down Local Kafka + Vault Demo Environment"
echo "===================================================="
echo ""

# Confirm before proceeding
read -p "⚠️  This will stop all services and remove containers. Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted."
    exit 1
fi

# Stop services
echo "🛑 Stopping Docker Compose services..."
docker compose down
echo "✅ Services stopped!"
echo ""

# Ask about volumes
read -p "🗑️  Do you want to remove all data volumes? This will delete all Kafka and Vault data. (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing volumes..."
    docker compose down -v
    echo "✅ Volumes removed!"
else
    echo "ℹ️  Volumes preserved. Data will persist until you explicitly remove them."
    echo "   To remove volumes later, run: docker compose down -v"
fi

echo ""
echo "✨ Teardown complete!"
echo ""
echo "💡 To start the demo again, run: ./setup.sh"
echo ""
