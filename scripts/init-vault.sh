#!/bin/bash

set -e

echo "🔐 Initializing Vault for Kafka Demo..."

# Check if VAULT_ADDR is set
if [ -z "$VAULT_ADDR" ]; then
    export VAULT_ADDR="http://localhost:8200"
fi

# Check if VAULT_TOKEN is set
if [ -z "$VAULT_TOKEN" ]; then
    echo "⚠️  VAULT_TOKEN not set. Please set it before running this script."
    echo "   For local dev mode, use: export VAULT_TOKEN='dev-only-token'"
    exit 1
fi

echo "✅ Vault Address: $VAULT_ADDR"

# Enable Transit secrets engine
echo "📝 Enabling Transit secrets engine..."
vault secrets enable -path=transit transit 2>/dev/null || echo "   Transit engine already enabled"

# Create encryption key for transit
echo "🔑 Creating transit encryption key..."
vault write -f transit/keys/transit \
    type="aes256-gcm96" \
    exportable=false \
    allow_plaintext_backup=false \
    derived=true 2>/dev/null || echo "   Transit key already exists"

# Enable Transform secrets engine (Enterprise only)
echo "📝 Enabling Transform secrets engine..."
if vault secrets enable -path=transform transform 2>/dev/null; then
    echo "   ✅ Transform engine enabled (Enterprise)"

    # Create transformation for credit card (Format Preserving Encryption)
    echo "🔧 Creating credit card transformation..."
    vault write transform/transformation/creditcard \
        type="fpe" \
        template="builtin/creditcard_number" \
        tweak_source="internal" \
        allowed_roles="payments" 2>/dev/null || echo "   Transformation already exists"

    # Create role for payments
    echo "👤 Creating payments role..."
    vault write transform/role/payments \
        transformations="creditcard" 2>/dev/null || echo "   Role already exists"
else
    echo "   ℹ️  Transform engine not available (Vault OSS)"
    echo "   💡 Transform secrets engine requires Vault Enterprise"
    echo "   💡 The demo will work with Transit encryption only"
fi

# Verify setup
echo ""
echo "✨ Vault initialization complete!"
echo ""
echo "Verifying setup..."
echo ""

# Display transit keys
echo "🔑 Transit keys:"
vault list transit/keys || echo "   No keys found"

echo ""
echo "🔧 Transform roles:"
vault list transform/role || echo "   No roles found"

echo ""
echo "🔐 Transform transformations:"
vault list transform/transformation || echo "   No transformations found"

echo ""
echo "✅ Vault is ready for the demo!"
echo ""
echo "You can now run the demo scripts:"
echo "  - python3 producer.py"
echo "  - python3 encryptor.py"
echo "  - python3 consumer_from_encrypted.py"
