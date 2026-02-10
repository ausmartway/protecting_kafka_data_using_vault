# Protecting Kafka Data with HashiCorp Vault

> **Encryption-as-a-Service for Streaming Platforms**
> Demonstrate how to protect sensitive data in Kafka pipelines using Vault's encryption capabilities

---

## Table of Contents

- [Overview](#overview)
- [The Problem: Data Leakage in Streaming Platforms](#the-problem-data-leakage-in-streaming-platforms)
- [The Solution: Vault as Encryption-as-a-Service](#the-solution-vault-as-encryption-as-a-service)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Demo Scenarios](#demo-scenarios)
- [Beyond Kafka](#beyond-kafka)
- [Troubleshooting](#troubleshooting)

---

## Overview

This project demonstrates how to protect sensitive data (PII, PCI) in Kafka messaging streams using [HashiCorp Vault](https://www.vaultproject.io/) as an Encryption-as-a-Service provider. It addresses the critical security concern: **when using managed Kafka services, platform administrators can potentially read message contents**.

### What You'll Learn

- **Per-field encryption** using Vault Transform and Transit engines
- **Envelope encryption** for efficient large payload handling
- **Key rotation** without application downtime
- **Format-Preserving Encryption (FPE)** for structured data

### Use Cases

This pattern applies to any streaming platform:
- Apache Kafka / Confluent Cloud
- AWS Kinesis, SQS, SNS
- Google Cloud Pub/Sub
- Azure Event Hubs
- Apache Spark Streaming

---

## The Problem: Data Leakage in Streaming Platforms

### The Data-at-Risk

Kafka caches messages to ensure delivery to consumers. While acceptable in on-premises deployments, the risk profile changes dramatically in cloud environments:

```
Risk Level:
On-Premises  ──────► Managed Cloud ──────► SaaS Kafka
     Low                  Medium                 High
```

### The Complication

Encrypting data at the application layer introduces significant complexity:

| Challenge | Description |
|-----------|-------------|
| **Key Management** | Applications need shared Data Encryption Keys (DEKs) and nonces/IVs |
| **Key Distribution** | DEKs must be protected in transit and at rest |
| **Key Rotation** | Regular rotation required for compliance |
| **Algorithm Compatibility** | Different languages support different encryption algorithms |
| **Operational Overhead** | Each application team implementing encryption is costly and error-prone |

---

## The Solution: Vault as Encryption-as-a-Service

HashiCorp Vault provides centralized encryption services that applications can consume via simple API calls, eliminating the need to manage keys directly.

### Vault Encryption Engines

| Engine | Use Case | Key Feature |
|--------|----------|-------------|
| **Transit** | General-purpose encryption | Centralized key management, versioning |
| **Transform (FPE)** | Structured data (credit cards, SSNs) | Preserves data format for business logic |
| **Transit (Envelope)** | Large payloads | Reduces Vault load for bulk encryption |

### Benefits

✅ **No direct key access** - Applications never see the DEKs
✅ **Unified encryption** - Same API across all applications and languages
✅ **Seamless rotation** - Rotate keys without application changes
✅ **Audit logging** - All encryption operations logged in Vault
✅ **Compliance** - Meet PCI-DSS, GDPR requirements with proven patterns

---

## Architecture

### Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                         ENCRYPTION FLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Producer App              Vault                 Kafka              │
│  ┌──────────┐           ┌──────────┐          ┌──────────┐         │
│  │ Plaintext│──────────▶│ Encrypt  │──────────▶│ Encrypted│         │
│  │  Data    │           │  API     │          │   Data   │         │
│  └──────────┘           └──────────┘          └──────────┘         │
│                                                             │        │
│                                                             ▼        │
│                                                    ┌──────────────┐  │
│                                                    │ Kafka Topics │  │
│                                                    │ - purchases  │  │
│                                                    │ - purchases_ │  │
│                                                    │   encrypted  │  │
│                                                    └──────────────┘  │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                         DECRYPTION FLOW                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Consumer App              Vault                 Kafka              │
│  ┌──────────┐           ┌──────────┐          ┌──────────┐         │
│  │ Plaintext│◀──────────│ Decrypt  │◀──────────│ Encrypted│         │
│  │  Data    │           │  API     │          │   Data   │         │
│  └──────────┘           └──────────┘          └──────────┘         │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### Envelope Encryption (Large Payloads)

```
┌──────────────────────────────────────────────────────────────────────┐
│                   ENVELOPE ENCRYPTION PATTERN                        │
├──────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  Producer Side                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ 1. Request DEK from Vault                                      │  │
│  │ 2. Vault returns encrypted DEK (wrapped with master key)       │  │
│  │ 3. Encrypt payload locally using DEK (AES-256-GCM)             │  │
│  │ 4. Send encrypted payload + encrypted DEK to Kafka             │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Kafka Message Structure:                                            │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Headers:                                                         │  │
│  │   X-encryptionkey: <vault:v1:encrypted-dek>                     │  │
│  │   X-filename: <original-filename>                               │  │
│  │ Body:                                                            │  │
│  │   {                                                              │  │
│  │     "nonce": "<base64-nonce>",                                   │  │
│  │     "ciphertext": "<hex-encoded-payload>",                       │  │
│  │     "tag": "<hex-auth-tag>"                                     │  │
│  │   }                                                              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
│  Consumer Side                                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ 1. Extract encrypted DEK from headers                           │  │
│  │ 2. Decrypt DEK using Vault                                      │  │
│  │ 3. Decrypt payload locally using DEK                            │  │
│  │ 4. Process plaintext data                                        │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Prerequisites

### Infrastructure

- **HashiCorp Vault Enterprise** with Advanced Data Protection (ADP) license
  - Transform secrets engine requires enterprise license
  - [Get a free Vault Enterprise trial](https://developer.hashicorp.com/vault/docs/enterprise/trial)

- **Confluent Cloud Account** (Free tier available)
  - Developer role gets free trial without expiry
  - [Sign up at Confluent Cloud](https://confluent.cloud/)

### Local Tools

```bash
# Check required tools
terraform --version    # >= 1.0
python3 --version      # >= 3.8
pip --version
```

### Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt
```

**Dependencies:**
- `confluent-kafka` - Kafka client library
- `hvac` - Vault API client
- `pycryptodome` - Cryptographic primitives for envelope encryption

---

## Quick Start

### Step 1: Provision Infrastructure

**Set up Confluent Cloud credentials:**

```bash
# After signing up, create a Cloud API key with global access
export CONFLUENT_CLOUD_API_KEY="<your-api-key>"
export CONFLUENT_CLOUD_API_SECRET="<your-api-secret>"
```

**Provision Kafka infrastructure:**

```bash
cd terraform/confluent_terraform
terraform init
terraform plan
terraform apply
```

**Retrieve Kafka credentials from Terraform output:**

```bash
# Get cluster ID, API key, and secret from Terraform outputs
terraform output -json
```

Update `getting_started.ini` with your Kafka cluster credentials:

```ini
[default]
bootstrap.servers=<your-kafka-bootstrap-servers>
security.protocol=SASL_SSL
sasl.mechanisms=PLAIN
sasl.username=<your-api-key>
sasl.password=<your-api-secret>
```

### Step 2: Configure Vault

**Provision Vault secret engines:**

```bash
cd terraform/vault_transform
export VAULT_ADDR="https://your-vault-server:8200"
export VAULT_TOKEN="<your-vault-token>"
export VAULT_NAMESPACE="<your-namespace>"  # if using namespaces

terraform init
terraform plan
terraform apply
```

This sets up:
- Transform secrets engine with `creditcard` transformation
- Transit secrets engine for encryption
- Role `payments` for credit card operations

### Step 3: Set Environment Variables

```bash
# Vault connection
export VAULT_ADDR="https://your-vault-server:8200"
export VAULT_TOKEN="<your-vault-token>"
export VAULT_NAMESPACE="<your-namespace>"  # if using namespaces

# For demo purposes, disable TLS verification (NOT for production)
export VAULT_SKIP_VERIFY=true
```

### Step 4: Verify Installation

```bash
# Test Python dependencies
python3 -c "import confluent_kafka, hvac, Crypto; print('All dependencies installed!')"
```

---

## Demo Scenarios

### Demo 1: The Problem - Plaintext Data is Visible

**Purpose:** Demonstrate that Kafka platform administrators can read message contents.

**Steps:**

1. **Open the Confluent Cloud console**
   - Navigate to: **Environments** → **Development** → **BASIC_DEMO_KAFKA_CLUSTER** → **Topics** → **purchases** → **Messages**

2. **Run the producer**

```bash
python3 producer.py
```

1. **Observe:** Messages appear in the browser with **plaintext** credit card numbers and addresses

**Sample Output:**
```json
{
  "Name": "John Doe",
  "Address": "123 Main Street, Anytown, USA",
  "credit_card": "4532-1234-5678-9010"
}
```

💡 **Key Insight:** Anyone with Kafka admin privileges can view sensitive PII and PCI data.

---

### Demo 2: Per-Field Encryption with Vault

**Purpose:** Demonstrate Vault's encryption capabilities for different data types.

**Encryption Methods:**
- **Credit Cards:** Format-Preserving Encryption (FPE) via Transform engine
  - Preserves format: `4532-1234-5678-9010` → `9876-5432-1098-7654`
  - Enables business logic on encrypted data

- **Addresses:** Standard encryption via Transit engine
  - Base64 encoded before encryption
  - Full ciphertext output

#### Part A: Encrypt Messages

1. **Open the encrypted topic in Confluent Cloud**
   - Navigate to: **Topics** → **purchases_encrypted** → **Messages**

2. **Run the encryptor** (consumes from `purchases`, encrypts, produces to `purchases_encrypted`)

```bash
# Terminal 1: Run producer to generate plaintext data
python3 producer.py

# Terminal 2: Run encryptor to encrypt data
python3 encryptor.py
```

1. **Observe in browser:** Encrypted messages appear with:
   - Credit card numbers encrypted but format preserved
   - Addresses fully encrypted (Base64 ciphertext)

**Encrypted Output:**
```json
{
  "Name": "John Doe",
  "Address": "vault:v1:abcd1234efgh5678...",
  "credit_card": "9876-5432-1098-7654"
}
```

#### Part B: Key Rotation

**Demonstrate Vault's automatic key versioning:**

1. **Rotate the encryption key in Vault**

```bash
# Rotate transit key
vault write -f transit/keys/rotate

# Or via API
curl -X POST \
  $VAULT_ADDR/v1/transit/keys/rotate \
  -H "X-Vault-Token: $VAULT_TOKEN"
```

1. **Run producer again** - New messages will be encrypted with the new key version

2. **Observation:** Both old and new messages can still be decrypted - Vault maintains key version history!

#### Part C: Decrypt Messages

```bash
# Terminal 3: Consumer decrypts messages automatically
python3 consumer_from_encrypted.py
```

**Decrypted Output:**
```json
{
  "Name": "John Doe",
  "Address": "123 Main Street, Anytown, USA",
  "credit_card": "4532-1234-5678-9010"
}
```

💡 **Key Insight:** Applications work with plaintext, but Kafka only stores encrypted data. Key rotation is transparent to applications.

---

### Demo 3: Envelope Encryption for Large Payloads

**Purpose:** Demonstrate efficient encryption for large files using the envelope encryption pattern.

**Why Envelope Encryption?**
- Sending large payloads to Vault creates network latency
- Vault CPU load increases with payload size
- Envelope encryption offloads bulk encryption to the client
- Only the Data Encryption Key (DEK) is encrypted/decrypted by Vault

#### Part A: Transfer Encrypted Files

1. **Open the large payload topic**
   - Navigate to: **Topics** → **purchases_large_encrypted** → **Messages**

2. **Prepare directories and files**

```bash
# Create source and destination directories
mkdir -p source destination

# Copy test files
cp test_file.txt source/
cp fakeaddress.txt source/
```

3. **Start the consumer** (Terminal 1)

```bash
python3 consumer_file_transfer.py
```

4. **Start the producer** (Terminal 2)

```bash
python3 producer_file_transfer.py
```

#### Part B: Observe the Process

**In Confluent Cloud browser:**
- Messages show encrypted content
- **Headers contain:**
  - `X-encryptionkey`: Encrypted DEK (wrapped by Vault)
  - `X-filename`: Original filename
- **Body contains:**
  - `nonce`: AES-GCM nonce
  - `ciphertext`: Hex-encoded encrypted file
  - `tag`: Authentication tag

**In consumer terminal:**
```text
Data Encryption Key from header: vault:v1:xyz789...
Data Encryption Key after decryption from Vault: aGVsbG8... (base64)
Decrypted file saved to: destination/received-test_file.txt
```

**In destination directory:**
```bash
ls -la destination/
# -rw-r--r-- received-test_file.txt
# -rw-r--r-- received-fakeaddress.txt
```

💡 **Key Insight:** Large files are encrypted/decrypted locally, while Vault only manages the DEKs. This scales to much larger payloads than sending everything to Vault.

---

## Beyond Kafka

The encryption patterns demonstrated in this project apply to **any streaming or messaging platform**:

### Compatible Platforms

| Platform | Encryption Pattern | Notes |
|----------|-------------------|-------|
| **Apache Kafka** | Per-field, Envelope | Direct compatibility |
| **Confluent Cloud** | Per-field, Envelope | Demo uses this platform |
| **AWS Kinesis** | Per-field, Envelope | Same Vault API calls |
| **AWS SQS/SNS** | Per-field, Envelope | Encrypt message bodies |
| **Google Pub/Sub** | Per-field, Envelope | Encrypt message data |
| **Azure Event Hubs** | Per-field, Envelope | Encrypt event bodies |
| **Apache Spark** | Per-field, Envelope | Encrypt RDD/DataFrame data |

### Implementation Pattern

```python
# Pseudocode for any platform
import hvac

client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)

# Encrypt before sending to platform
def encrypt_data(plaintext):
    response = client.secrets.transit.encrypt_data(
        name='transit',
        plaintext=base64.b64encode(plaintext).decode()
    )
    return response['data']['ciphertext']

# Send encrypted data to any platform
platform.send(encrypted_data)

# Decrypt after receiving from platform
def decrypt_data(ciphertext):
    response = client.secrets.transit.decrypt_data(
        name='transit',
        ciphertext=ciphertext
    )
    return base64.b64decode(response['data']['plaintext'])
```

---

## Troubleshooting

### Common Issues

#### Issue: "No such topic" error

**Solution:** Ensure Terraform has successfully created the topics:

```bash
cd terraform/confluent_terraform
terraform apply
```

---

#### Issue: "SASL authentication failed"

**Solution:** Verify Kafka credentials in `getting_started.ini` match your Confluent Cloud API key:

```bash
# Verify credentials from Terraform output
cd terraform/confluent_terraform
terraform output kafka_api_key
terraform output kafka_api_secret
```

---

#### Issue: "Connection refused" to Vault

**Solution:** Check Vault is accessible and TLS settings:

```bash
# Test Vault connection
curl -k $VAULT_ADDR/v1/sys/health

# If using self-signed cert, set skip verify
export VAULT_SKIP_VERIFY=true
```

---

#### Issue: "Permission denied" on Transform engine

**Solution:** Verify Transform engine is enabled and you have the correct license:

```bash
# Check enabled engines
vault secrets list

# Verify license (requires enterprise)
vault read sys/license
```

---

#### Issue: Python import errors

**Solution:** Reinstall dependencies:

```bash
# Uninstall and reinstall
pip uninstall -y confluent-kafka hvac pycryptodome
pip install -r requirements.txt

# Verify installation
python3 -c "import confluent_kafka, hvac, Crypto"
```

---

#### Issue: Consumer doesn't receive messages

**Solution:** Check consumer group offset:

```bash
# Use --reset flag to start from beginning
python3 consumer_from_encrypted.py --reset
```

---

### Debug Mode

Enable verbose logging for troubleshooting:

```python
# Add to your Python scripts
import logging
logging.basicConfig(level=logging.DEBUG)

# Or set environment variable
export CONFLUENT_KAFKA_DEBUG=consumer,broker,topic
```

---

### Getting Help

- **Vault Documentation:** https://developer.hashicorp.com/vault/docs
- **Confluent Kafka Python Client:** https://docs.confluent.io/platform/clients/README.html
- **Vault Community Forum:** https://discuss.hashicorp.com/c/vault

---

## Security Considerations

### Production Deployment Checklist

- [ ] Enable TLS verification for Vault connections
- [ ] Use Vault's Kubernetes auth or AWS auth instead of tokens
- [ ] Implement proper secret management for Kafka credentials
- [ ] Enable Vault audit logging for compliance
- [ ] Use separate Vault namespaces for different environments
- [ ] Implement automated key rotation policies
- [ ] Monitor Vault performance and scale as needed

### Credential Security

⚠️ **Never commit credentials to version control**

```bash
# .gitignore
getting_started.ini
.env
*.pem
```

Store sensitive configuration in environment variables or secure secret managers.

---

## Contributing

This is a demonstration project. Feel free to submit issues or pull requests for:
- Bug fixes
- Documentation improvements
- Additional encryption pattern examples
- Support for other streaming platforms

---

## License

This project is provided as-is for educational and demonstration purposes.

---

## Resources

- [HashiCorp Vault Documentation](https://developer.hashicorp.com/vault/docs)
- [Confluent Cloud Documentation](https://docs.confluent.cloud/)
- [Vault Transform Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/transform)
- [Vault Transit Secrets Engine](https://developer.hashicorp.com/vault/docs/secrets/transit)
- [Format-Preserving Encryption](https://en.wikipedia.org/wiki/Format-preserving_encryption)

---

**Made with ❤️ for the DevOps community**
