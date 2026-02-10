# Local Demo - User Guide

## 🎯 Purpose

This demo shows how to protect sensitive data in Kafka messages using HashiCorp Vault for encryption. You'll learn how to:
- Encrypt sensitive fields before sending to Kafka
- Use Vault Transit for general encryption (addresses, documents)
- Use Vault Transform for format-preserving encryption (credit cards, SSNs)
- Apply envelope encryption for large payloads

**Target Audience**: Messaging specialists and data protection professionals who need to secure Kafka data.

---

## 🚀 Quick Start (5 minutes)

### Prerequisites

```bash
# Check Docker is running
docker --version
docker compose version

# Check Python
python3 --version
```

### Start the Demo

```bash
# 1. Navigate to project
cd protecting_kafka_data_using_vault

# 2. Install Python dependencies
python3 -m pip install -r requirements.txt

# 3. Start everything (one command!)
./setup.sh
```

That's it! All services are now running.

---

## 🔑 Access Credentials & URLs

### Vault Enterprise UI

**URL**: http://localhost:8200/ui
**Token**: `dev-only-token`

**What you'll see**:
- Transit secrets engine at `transit/`
- Transform secrets engine at `transform/`
- Encryption keys and transformations

**Why explore Vault UI**:
- View encryption keys and their versions
- Monitor encryption/decryption operations
- Test Transform FPE templates interactively
- Understand key rotation workflow

### Kafka UI

**URL**: http://localhost:8080

**What you'll see**:
- Topics: `purchases`, `purchases_encrypted`, `purchases_large_encrypted`
- Consumer groups
- Broker information

**Why explore Kafka UI**:
- See messages in plaintext vs encrypted format
- Understand topic structure and partitions
- Monitor consumer lag and offsets
- Verify data at rest in Kafka

### Kafka Broker

**URL**: localhost:9092
**No authentication required** (local development)

---

## 📚 Demo Walkthroughs

### Demo 1: See the Risk (Plaintext Messages)

**Purpose**: Understand why encrypting Kafka data matters

**Steps**:
1. Open Kafka UI: http://localhost:8080
2. Navigate to Topics → `purchases` → Messages
3. In terminal, run:
   ```bash
   python3 producer.py
   ```

**What you'll see**:
- Messages with names, addresses, and **credit card numbers in plaintext**
- Anyone with Kafka admin access can read this sensitive data

**Why this matters**:
- In cloud or SaaS Kafka, platform administrators can see your data
- Data at rest in Kafka is vulnerable if infrastructure is compromised
- Regulations (PCI-DSS, GDPR) require encryption of sensitive data

---

### Demo 2: Per-Field Encryption with Vault

**Purpose**: Encrypt only sensitive fields while keeping message structure

**Architecture**:
```
Plaintext Topic      Encryptor Service        Encrypted Topic
    (purchases)  →  [Vault Transit +       →  (purchases_encrypted)
                      Transform FPE]
```

**Steps** (open 3 terminals):

**Terminal 1 - Start the Encryptor**:
```bash
# Consumes from purchases, encrypts, produces to purchases_encrypted
python3 encryptor.py
```

**Terminal 2 - Start the Consumer**:
```bash
# Consumes from purchases_encrypted, decrypts, displays
python3 consumer_from_encrypted.py
```

**Terminal 3 - Generate Traffic**:
```bash
# Produces plaintext messages
python3 producer.py
```

**In Kafka UI** (http://localhost:8080):
1. Navigate to Topics → `purchases_encrypted` → Messages
2. Notice:
   - **Addresses** are encrypted ciphertext (Vault Transit)
   - **Credit cards** are encrypted but **still 16 digits** (Vault Transform FPE)

**Why this approach**:
- **Per-field encryption**: Only encrypt what's sensitive
- **Format preservation**: Credit cards stay valid credit card numbers
- **Searchable fields**: Non-sensitive fields (names, IDs) remain queryable
- **Zero trust**: Producers don't need decryption keys

**Encryption Types**:

| Field | Vault Engine | Method | Benefit |
|-------|-------------|--------|---------|
| Address | Transit | AES-256-GCM | Strong encryption, supports key rotation |
| Credit Card | Transform FPE | Format-preserving | Maintains validation, length, checksum |

---

### Demo 3: Large File Encryption

**Purpose**: Efficient encryption for large payloads using envelope encryption

**Problem with Vault-only encryption**:
- Sending large files to Vault for encryption is slow
- Creates CPU bottleneck on Vault servers
- High network latency

**Solution - Envelope Encryption**:
```
1. Generate DEK (Data Encryption Key) in Vault
2. Encrypt DEK with Vault master key
3. Encrypt file locally using DEK
4. Send encrypted file + encrypted DEK via Kafka
```

**Steps**:

**Prepare test files**:
```bash
# Copy some files to encrypt
cp test_file.txt source/
cp large-set-of-info.json source/
```

**Terminal 1 - Consumer**:
```bash
# Receives encrypted files, decrypts DEK from Vault, decrypts files
python3 consumer_file_transfer.py
```

**Terminal 2 - Producer**:
```bash
# Generates DEK, encrypts files locally, sends to Kafka
python3 producer_file_transfer.py
```

**Verify**:
```bash
# Files appear in destination/ directory
ls -la destination/
```

**In Kafka UI**:
- Topic: `purchases_large_encrypted`
- Message body: Encrypted file content
- HTTP Headers: Encrypted DEK + filename

**Why envelope encryption**:
- **Scalability**: Vault only handles small DEK operations
- **Performance**: Large files encrypted/decrypted locally
- **Security**: Each file gets unique DEK (limits blast radius)
- **Industry standard**: Used by AWS KMS, GCP KMS, Azure Key Vault

---

## 🔐 Vault Encryption Engines Explained

### Transit Secrets Engine

**Use case**: General-purpose encryption

**How it works**:
1. Send plaintext to Vault
2. Vault encrypts with master key (AES-256-GCM)
3. Returns ciphertext
4. Store ciphertext anywhere (Kafka, database, files)

**Key features**:
- **Key versioning**: Automatic tracking of key versions
- **Key rotation**: Change keys without re-encrypting data
- **Convergent encryption**: Same plaintext → same ciphertext (for deduplication)

**In this demo**: Encrypts address fields

### Transform Secrets Engine

**Use case**: Format-preserving encryption (FPE)

**How it works**:
1. Send sensitive data (credit card, SSN, phone number)
2. Vault transforms while maintaining format
3. Encrypted output is valid same format as input

**Example**:
```
Plaintext:  4532-1234-5678-9010
Encrypted:  7891-4567-8901-2345
```

**Why FPE matters**:
- **Validation passes**: Encrypted credit cards pass Luhn checksum
- **No schema changes**: Database columns don't need modification
- **Complex logic**: Applications can process encrypted data

**In this demo**: Encrypts credit card numbers

---

## 🛠️ Environment Variables

The setup script automatically configures these:

```bash
# Vault connection
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-only-token"
export VAULT_NAMESPACE=""

# Kafka connection
# Configured in getting_started.ini (localhost:9092)
```

---

## 🛑 Stop the Demo

```bash
./teardown.sh
```

This stops all containers. You'll be prompted whether to remove data volumes.

---

## 🐛 Troubleshooting

### "Vault token not set"

```bash
export VAULT_TOKEN="dev-only-token"
```

### "Connection refused" on Kafka

```bash
# Check if services are running
docker compose ps

# Restart if needed
./teardown.sh
./setup.sh
```

### Python module not found

```bash
python3 -m pip install -r requirements.txt
```

### Port already in use

```bash
# Check what's using the port
lsof -i :9092  # Kafka
lsof -i :8200  # Vault
lsof -i :8080  # Kafka UI

# Stop conflicting service or change port in docker-compose.yml
```

---

## 📖 Why This Matters

### For Messaging Specialists

Kafka is a message bus, not a message protector. Your data security strategy:
- ✅ **Encrypt at source** (producers) - Before sending to Kafka
- ✅ **Decrypt at destination** (consumers) - After receiving from Kafka
- ❌ **Don't trust infrastructure** - Platform admins shouldn't see your data

### For Data Protection Specialists

Vault provides **Encryption as a Service**:
- **No key management in applications** - Apps call Vault API
- **Centralized encryption policies** - Enforce encryption standards
- **Audit trail** - All encryption/decryption logged
- **Key rotation** - Change keys without updating applications

---

## 🎓 Key Concepts

### Zero Trust Architecture

Traditional trust model:
```
Producer → [Trusted Kafka] → Consumer
```

Zero trust model:
```
Producer → [Encrypted] → [Untrusted Kafka] → [Decrypted] → Consumer
           ↑                              ↑
        Vault API                    Vault API
```

### Defense in Depth

1. **Transit encryption**: TLS for network security
2. **At-rest encryption**: Vault for data security
3. **Key management**: Vault for key lifecycle
4. **Access control**: Vault policies for authorization

### Regulatory Compliance

This demo helps with:
- **PCI-DSS**: Credit card encryption (FPE)
- **GDPR**: Personal data protection (addresses)
- **Data sovereignty**: Control encryption keys
- **Audit requirements**: Vault logs all operations

---

## 📚 Next Steps

- **Explore Vault UI**: http://localhost:8200/ui
- **Try key rotation**: Rotate the transit key and see versioning
- **Read the main README**: More detailed architecture discussion
- **Confluent Cloud version**: See `terraform/confluent_terraform/` for cloud deployment

---

## 🆘 Need Help?

1. **Check the logs**: `docker compose logs vault` or `docker compose logs kafka`
2. **Verify services**: `docker compose ps`
3. **Review configuration**: Check `getting_started.ini` and `.env`

**Remember**: This is a local demo environment. For production:
- Use proper authentication
- Enable TLS for Vault
- Use Raft storage backend
- Implement proper access policies
