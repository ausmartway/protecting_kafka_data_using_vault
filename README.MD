# Protecting Kafka Data Using Vault

This demo shows how to protect sensitive data in Kafka messages using HashiCorp Vault for encryption as a service.

## The Problem

When you send data to Kafka, the platform caches it. This creates a risk:

- ✅ **On-premises Kafka**: Risk is acceptable (you control infrastructure)
- ⚠️ **Public cloud Kafka**: Risk increases (cloud provider has access)
- ❌ **SaaS Kafka**: Risk is highest (platform administrators can see your data)

**The solution**: Encrypt data **before** sending to Kafka, decrypt **after** receiving.

## Why This Is Hard

Implementing encryption yourself is difficult because:

1. **Key Management**: Applications need shared Data Encryption Keys (DEKs)
2. **Nonces/IVs**: Must be unique for each encryption operation
3. **Key Rotation**: Encryption keys must be rotated regularly
4. **Algorithm Compatibility**: All producers/consumers must use same algorithms
5. **Cross-Language Support**: Not all languages have mature encryption libraries

## The Solution: Vault Encryption as a Service

HashiCorp Vault provides encryption as a service with multiple engines:

### Transit Secrets Engine
- **Use case**: General-purpose encryption
- **How it works**: Send plaintext to Vault → Get ciphertext back
- **Benefits**: No key management in applications, automatic key versioning

### Transform Secrets Engine (FPE)
- **Use case**: Format-preserving encryption (credit cards, SSNs, phone numbers)
- **How it works**: Encrypts while maintaining data format
- **Benefits**: Encrypted data passes validation, no schema changes

### Envelope Encryption
- **Use case**: Large payloads (files, documents)
- **How it works**: Generate DEK in Vault, encrypt data locally
- **Benefits**: Scalable, reduces Vault load, industry-standard approach

## Demo Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Your Application                       │
│                  (Producer / Consumer)                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    Encryption/Decryption API Calls
                             │
                             ▼
                    ┌─────────────────┐
                    │   Vault Ent.    │
                    │                 │
                    │  ┌───────────┐  │
                    │  │ Transit   │  │  ← General encryption
                    │  │ (AES-256) │  │
                    │  └───────────┘  │
                    │                 │
                    │  ┌───────────┐  │
                    │  │Transform  │  │  ← Format-preserving
                    │  │   (FPE)   │  │
                    │  └───────────┘  │
                    └─────────────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │     Kafka       │
                    │   (localhost)   │
                    └─────────────────┘
```

## Quick Start

### Option 1: Local Demo (Recommended)

Run everything on your laptop:

```bash
# Clone and setup
git clone <repository-url>
cd protecting_kafka_data_using_vault

# Install dependencies
python3 -m pip install -r requirements.txt

# Start everything (one command!)
./setup.sh
```

**Access Points**:
- **Vault UI**: http://localhost:8200/ui (token: `dev-only-token`)
- **Kafka UI**: http://localhost:8080
- **Kafka Broker**: localhost:9092

**Detailed Guide**: See [USER_GUIDE.md](USER_GUIDE.md) for walkthroughs

### Option 2: Confluent Cloud

Requires Confluent Cloud account:

```bash
cd terraform/confluent_terraform
terraform init
terraform plan
terraform apply
```

See the original [Confluent Cloud setup](#confluent-cloud-setup) section below.

## Demo Cases

### Demo 1: Plaintext Messages (Baseline)

**Purpose**: See the security risk of unencrypted Kafka data

```bash
python3 producer.py
```

Open Kafka UI (http://localhost:8080) → Topics → `purchases` → Messages

**Result**: You can see names, addresses, and credit card numbers in plaintext!

**Why this matters**: Anyone with Kafka admin access can read sensitive data.

### Demo 2: Per-Field Encryption

**Purpose**: Encrypt only sensitive fields while keeping message structure

**Terminal 1** (Encryptor):
```bash
python3 encryptor.py
```

**Terminal 2** (Consumer):
```bash
python3 consumer_from_encrypted.py
```

**Terminal 3** (Producer):
```bash
python3 producer.py
```

**In Kafka UI**: Topics → `purchases_encrypted` → Messages

**Result**:
- Addresses are encrypted (Transit AES-256-GCM)
- Credit cards are encrypted but still 16 digits (Transform FPE)

### Demo 3: Large File Transfer

**Purpose**: Efficient encryption for large payloads

```bash
# Copy test files
cp test_file.txt source/

# Terminal 1: Consumer
python3 consumer_file_transfer.py

# Terminal 2: Producer
python3 producer_file_transfer.py
```

**Result**: Files encrypted with envelope encryption, decrypted in destination/

## Encryption Explained

### Transit Encryption (Addresses)

**Process**:
1. Producer sends plaintext address to Vault
2. Vault encrypts with AES-256-GCM
3. Returns ciphertext
4. Stored in Kafka as encrypted field

**Key Features**:
- Automatic key versioning
- Key rotation without re-encryption
- Convergent encryption option

### Transform FPE (Credit Cards)

**Process**:
1. Producer sends credit card to Vault
2. Vault transforms while maintaining format
3. Returns encrypted credit card (still valid 16 digits)
4. Stored in Kafka

**Example**:
```
Plaintext:  4532-1234-5678-9010
Encrypted:  7891-4567-8901-2345
```

**Benefits**:
- Passes Luhn checksum validation
- No database schema changes
- Applications can process encrypted data

### Envelope Encryption (Large Files)

**Process**:
1. Generate unique DEK in Vault
2. Encrypt DEK with Vault master key
3. Encrypt file locally using DEK
4. Send encrypted file + encrypted DEK via Kafka

**Benefits**:
- Vault only handles small DEK operations
- Large files encrypted locally (scalable)
- Industry-standard approach (AWS KMS, GCP KMS)

## Vault Credentials & Configuration

### Environment Variables

```bash
# Vault connection (set automatically by ./setup.sh)
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-only-token"
export VAULT_NAMESPACE=""
```

### Kafka Configuration

Configured in `getting_started.ini`:
- Bootstrap servers: `localhost:9092`
- No authentication (local development)
- Topics: `purchases`, `purchases_encrypted`, `purchases_large_encrypted`

## Stop the Demo

```bash
./teardown.sh
```

Optionally remove data volumes for clean slate.

## Troubleshooting

See [USER_GUIDE.md](USER_GUIDE.md) for detailed troubleshooting.

Common issues:
- **Vault token not set**: `export VAULT_TOKEN="dev-only-token"`
- **Port conflicts**: Check if ports 8200, 9092, or 8080 are in use
- **Python modules**: `python3 -m pip install -r requirements.txt`

## Beyond Kafka

This encryption pattern applies to any streaming platform:
- AWS Kinesis
- AWS SQS/SNS
- Google Cloud Pub/Sub
- Azure Event Hubs
- Apache Spark Streaming

## Confluent Cloud Setup

<details>
<summary>Click to expand Confluent Cloud instructions</summary>

### Prerequisites

- Vault Enterprise with ADP license
- Confluent Cloud account (free tier available)

### Setup Confluent Cloud

1. Go to [confluent.cloud](https://confluent.cloud/) and sign up
2. Create Cloud API key with global access:
   ```bash
   export CONFLUENT_CLOUD_API_SECRET=<your secret>
   export CONFLUENT_CLOUD_API_KEY=<your key>
   ```

3. Deploy infrastructure with Terraform:
   ```bash
   cd terraform/confluent_terraform
   terraform init
   terraform plan
   terraform apply
   ```

4. Update `getting_started.ini` with cluster URL and API keys from Terraform output

### Topics Created

- `purchases` - Plaintext messages
- `purchases_encrypted` - Per-field encrypted messages
- `purchases_large_encrypted` - Large payloads with envelope encryption

</details>

## Learn More

- [Vault Transit Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/transit)
- [Vault Transform Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/transform)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [PCI-DSS Requirements](https://www.pcisecuritystandards.org/)
- [GDPR Compliance](https://gdpr.eu/)

## License

This demo uses HashiCorp Vault Enterprise. For production use, ensure you have appropriate licensing.
