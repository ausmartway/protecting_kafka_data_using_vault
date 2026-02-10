# Local Kafka + Vault Demo - Quick Start Guide

## One-Command Setup

```bash
# From the project root directory
./setup.sh
```

That's it! The script will:
✅ Start Kafka, Zookeeper, Vault, and Kafka UI
✅ Create all required topics
✅ Initialize Vault with Transit and Transform engines
✅ Set up configuration files

## What You Get

| Service | URL | Purpose |
|---------|-----|---------|
| **Kafka** | localhost:9092 | Message broker |
| **Vault** | http://localhost:8200 | Encryption service |
| **Kafka UI** | http://localhost:8080 | Web interface to view topics |

## Running the Demos

### Demo 1: Plaintext Messages (Baseline)
```bash
python3 producer.py
```
Open Kafka UI → Topics → `purchases` → Messages
👀 You can see all the sensitive data in plaintext!

### Demo 2: Per-Field Encryption
```bash
# Terminal 1: Encryptor
python3 encryptor.py

# Terminal 2: Consumer
python3 consumer_from_encrypted.py

# Terminal 3: Producer
python3 producer.py
```
Open Kafka UI → Topics → `purchases_encrypted` → Messages
🔒 Data is encrypted! Credit cards keep format, addresses are ciphertext.

### Demo 3: Large File Encryption
```bash
# Copy some test files
cp test_file.txt source/

# Terminal 1: Consumer
python3 consumer_file_transfer.py

# Terminal 2: Producer
python3 producer_file_transfer.py
```
Check the `destination/` folder - files are decrypted there!
📦 Uses envelope encryption with per-file DEKs.

## Cleanup

```bash
./teardown.sh
```

## Troubleshooting

**Issue**: Port already in use
```bash
# Check what's using the port
lsof -i :9092  # Kafka
lsof -i :8200  # Vault

# Stop the service or change port in docker-compose.yml
```

**Issue**: Scripts can't connect
```bash
# Ensure you're using local config
cp getting_started.local.ini getting_started.ini
```

**Issue**: Everything is broken
```bash
# Clean restart
./teardown.sh
# When prompted, choose 'y' to remove volumes
./setup.sh
```

## Environment Variables

```bash
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-only-token"
export VAULT_NAMESPACE=""
```

These are automatically set by `./setup.sh`.

## Key Concepts Demonstrated

1. **Transit Secrets Engine**: General-purpose encryption (AES-256-GCM)
2. **Transform Secrets Engine**: Format-preserving encryption (FPE)
3. **Per-Field Encryption**: Encrypt only sensitive fields
4. **Envelope Encryption**: Efficient large payload encryption
5. **Key Rotation**: Seamless version management

## Next Steps

- Read the full README.md for detailed explanations
- Explore the Kafka UI at http://localhost:8080
- Check Vault UI at http://localhost:8200/ui
- Try rotating keys: `docker exec vault vault write -f transit/keys/transit/rotate`
- Review the refactoring summary: `docs/REFACTORING_SUMMARY.md`

## Architecture

```
┌─────────────────┐
│  Producer.py    │ Generates PII/PCI data
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Kafka (Local)  │ Stores messages
│  localhost:9092│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Encryptor.py   │ Consumes, encrypts fields
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Vault (Local)  │ Encryption as a Service
│  localhost:8200│ - Transit (AES-256)
│                 │ - Transform (FPE)
└─────────────────┘
```

---

**Questions?** See README.md or docs/REFACTORING_SUMMARY.md
