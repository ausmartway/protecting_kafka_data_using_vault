#!/bin/bash

set -e

echo "📚 Creating Kafka topics for demo..."

# Wait for Kafka to be ready
echo "⏳ Waiting for Kafka to be ready..."
until docker exec kafka kafka-broker-api-versions --bootstrap-server localhost:9092 2>/dev/null; do
    echo "   Kafka not ready yet, waiting 5 seconds..."
    sleep 5
done

echo "✅ Kafka is ready!"

# Create topics
echo "📝 Creating topics..."

# Topic 1: purchases (plaintext)
docker exec kafka kafka-topics --create \
    --if-not-exists \
    --topic purchases \
    --bootstrap-server localhost:9092 \
    --partitions 1 \
    --replication-factor 1 && echo "   ✅ Created topic: purchases" || echo "   ⚠️  Topic 'purchases' may already exist"

# Topic 2: purchases_encrypted (encrypted fields)
docker exec kafka kafka-topics --create \
    --if-not-exists \
    --topic purchases_encrypted \
    --bootstrap-server localhost:9092 \
    --partitions 1 \
    --replication-factor 1 && echo "   ✅ Created topic: purchases_encrypted" || echo "   ⚠️  Topic 'purchases_encrypted' may already exist"

# Topic 3: purchases_large_encrypted (large payloads with DEK)
docker exec kafka kafka-topics --create \
    --if-not-exists \
    --topic purchases_large_encrypted \
    --bootstrap-server localhost:9092 \
    --partitions 1 \
    --replication-factor 1 \
    --config max.message.bytes=8388608 && echo "   ✅ Created topic: purchases_large_encrypted" || echo "   ⚠️  Topic 'purchases_large_encrypted' may already exist"

echo ""
echo "✨ Topics created successfully!"
echo ""
echo "Listing all topics:"
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

echo ""
echo "✅ Kafka is ready for the demo!"
