# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This demo shows how to protect sensitive data in Kafka messages using HashiCorp Vault for encryption as a service. It demonstrates three encryption patterns:
1. **Plaintext baseline** - Shows the security risk
2. **Per-field encryption** - Vault Transit (AES-256-GCM) and Transform FPE
3. **Envelope encryption** - Large payload encryption with DEKs

## Architecture

```
Producer → Vault (encrypt) → Kafka → Consumer → Vault (decrypt)
```

**Key Components**:
- **Vault Enterprise 1.21-ent**: Transit and Transform secrets engines
- **Kafka 7.7.0**: Message broker (local Docker)
- **Python 3.14+**: Producer/consumer scripts
- **hvac 2.3.0**: Vault API client

## Build and Run Commands

### Local Demo (Primary Use Case)

```bash
# Start all services
./setup.sh

# Stop all services
./teardown.sh
```

### Python Scripts

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Demo 1: Plaintext messages (baseline)
python3 producer.py

# Demo 2: Per-field encryption (3 terminals)
python3 encryptor.py          # Terminal 1
python3 consumer_from_encrypted.py  # Terminal 2
python3 producer.py           # Terminal 3

# Demo 3: Large file transfer (2 terminals)
python3 producer_file_transfer.py
python3 consumer_file_transfer.py
```

## Conventions

### Docker Compose
- **Use `docker compose`** (v2), NOT `docker-compose` (deprecated v1)
- All services defined in `docker-compose.yml`
- Vault uses dev mode with token `dev-only-token`

### Vault Configuration
- **Transit engine**: Path `transit/`, key name `transit`
- **Transform engine**: Path `transform/`, transformation `creditcard`, role `payments`
- Scripts auto-initialize Vault on first run

### Kafka Configuration
- Local broker: `localhost:9092`
- Topics auto-created by scripts
- Configuration in `getting_started.ini`

### Python Environment
- **Minimum Python**: 3.13
- **Tested on**: 3.14.2
- **hvac version**: 2.3.0 (backward compatible with 1.x API)

## File Organization

```
protecting_kafka_data_using_vault/
├── producer.py                    # Plaintext message producer
├── consumer.py                    # Plaintext message consumer
├── encryptor.py                   # Encrypts messages from Kafka
├── consumer_from_encrypted.py     # Decrypts messages from Kafka
├── producer_file_transfer.py      # File encryption demo
├── consumer_file_transfer.py      # File decryption demo
├── transformer.py                 # LEGACY - contains hardcoded creds
├── getting_started.ini            # Kafka configuration
├── setup.sh                       # Start all services
├── teardown.sh                    # Stop all services
├── docker-compose.yml             # Service definitions
├── scripts/                       # Vault initialization scripts
│   ├── init-vault.sh
│   └── create-topics.sh
├── source/                        # Files to encrypt
└── destination/                   # Decrypted files
```

## Important Notes

### Deprecated Files
- **transformer.py**: Legacy prototype with hardcoded Vault token, not integrated with current demo flow

### Environment Variables
- **Required**: `VAULT_ADDR`, `VAULT_TOKEN`, `VAULT_NAMESPACE`
- Set automatically by `setup.sh` from `.env` file
- **Never commit `.env`** to git (already in .gitignore)

### Version Compatibility
- **hvac 2.x migration**: Complete - code uses backward-compatible API
- **Python 3.14**: Fully tested and compatible
- **Vault Enterprise**: Required for Transform FPE (credit card encryption)
- **Vault OSS**: Works for Transit encryption only

## Development Workflow

1. **Install dependencies**: `python3 -m pip install -r requirements.txt`
2. **Start services**: `./setup.sh`
3. **Run demos**: See USER_GUIDE.md for detailed walkthroughs
4. **Stop services**: `./teardown.sh`
5. **Check logs**: `docker compose logs vault` or `docker compose logs kafka`

## Documentation

- **README.MD**: Main documentation with architecture and quick start
- **USER_GUIDE.md**: Step-by-step demo walkthroughs
- **VERSION_ANALYSIS.md**: Version status and upgrade recommendations
- **CHANGELOG.md**: Version history and changes
- **DOCUMENTATION_ANALYSIS.md**: Documentation audit report
