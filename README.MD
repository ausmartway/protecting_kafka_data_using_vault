# Protecting data before sending to Kafka

## What is Kafka

Kafka is a distributed streaming platform that is used for building real-time data pipelines and streaming applications

It uses a publish-subscribe messaging model where data is produced by producers and consumed by consumers. Producers write data to Kafka topics, and consumers read data from those topics.

## Risk of data leaking

In order to make sure data is sent to consumers , the data is cached at Kafka. This creates a risk of leaking. The risk is considered acceptable when Kafka infrastructure runs on-premises. The risk increases when Kafka infrustructure runs on public cloud. It further increases when using a SaaS Kafka.

Ideally the team running the Kafka platform should not be responsible for this risk. Instead, producers shoud be encouraged to encrypt data before it is sent to Kafka.

## Complications

So it is now Kafka producers and consumers responsiblity to encrypt and decrypt the data. This is not easy.

In order to do data encrypt and decrypt operations, applications need a shared Data Encryption Key, and single use only [nonce or IV](https://www.oreilly.com/library/view/secure-programming-cookbook/0596003943/ch04s09.html) between encryptor and decryptor, if they are shared without protection, then data is at risk of leaking. Protection means many things, including frequent rotation and encryption in transit and at rest.

The Encryption Algorithm is also an important factor to consider. Producers and consumers need to share the same arlgorithm and mode. Not all languages have mature encryption libraries accross all arlgorisms and modes.

With those difficulties and limitations, letting application teams do encryption and decryption by themselves is costly in the long run.

## Solutions

HashiCorp Vault supports many ways of encryption, including [Transit](https://developer.hashicorp.com/vault/docs/secrets/transit), [Format Preserving Encryption](https://developer.hashicorp.com/vault/docs/secrets/transform#format-preserving-encryption), and [Tokenisation](https://developer.hashicorp.com/vault/docs/secrets/transform#tokenization). Each one is suited for different use cases.

Vault transit secret engine can be considered a general purpose Encryption as a Service that is easily accessible via API calls. Applications can send plaintext data to a Vault end point for encryption, or ciphertext for decryption, without the need to access the DEK or encryption arlgorithm and mode.

Format Preserving Encryption operates in a similar fashion and is designed to encrypt the data while keeping data format intact.

## demo setup

The demo code that follows allows you to setup Kafka Producers using Vault for Encryption as a Service. The examples provided show both transit encrption and format preserving encrption and demonstrate that without much trouble applications teams can leverage Vault as their EaaS provider consistently on any cloud, or with any platform.

## Deployment Options

You can run this demo in two ways:

1. **🏠 Local Demo (Recommended)**: Run everything on your laptop using Docker Compose - no external accounts required
2. **☁️ Confluent Cloud**: Use Confluent Cloud SaaS (original setup - requires account)

---

## Local Demo Setup (Recommended)

The local demo runs Kafka, Zookeeper, and Vault on your machine using Docker Compose. This approach offers several advantages:

✅ **No external dependencies** - Everything runs locally
✅ **Works offline** - No internet connection required
✅ **Free** - No Confluent Cloud account needed
✅ **Fast** - Local network, no latency
✅ **Easy reset** - Clean slate with one command
✅ **Educational** - See all components working together

### Prerequisites

Before starting, ensure you have:

* **Docker** - [Install Docker](https://docs.docker.com/get-docker/)
* **Docker Compose v2** - Included with Docker Desktop or [install separately](https://docs.docker.com/compose/install/)
* **Python 3.8+** with pip
* **Vault Enterprise License** (Optional) - For Transform secrets engine (FPE). Download from [HashiCorp Portal](https://portal.hashicorp.com)
  * 💡 *The demo works with Vault OSS for Transit encryption. Transform FPE (credit card format-preserving encryption) requires Enterprise*

### Quick Start

1. **Clone and navigate to the project**:
```bash
cd protecting_kafka_data_using_vault
```

2. **Install Python dependencies**:
```bash
python3 -m pip install -r requirements.txt
```

3. **Set up environment variables** (optional):
```bash
# Copy the example environment file
cp .env.example .env

# For Vault Enterprise with Transform (FPE) support:
# 1. Add your Vault Enterprise image to .env:
#    VAULT_IMAGE=hashicorp/vault-enterprise:1.17.0-ent
# 2. Place your license file at: ./vault.hclic
# 3. Uncomment and update the VAULT_LICENSE_PATH in docker-compose.yml
#
# For Vault OSS (Transit encryption only):
# No additional setup needed - just run ./setup.sh
```

4. **Start the demo environment**:
```bash
./setup.sh
```

This script will:
* Start Kafka, Zookeeper, Vault, and Kafka UI containers
* Wait for services to be healthy
* Create Kafka topics (`purchases`, `purchases_encrypted`, `purchases_large_encrypted`)
* Initialize Vault with Transit and Transform secrets engines
* Set up the `getting_started.ini` configuration file

5. **Verify services are running**:
```bash
# Check Docker containers
docker compose ps

# You should see: zookeeper, kafka, vault, kafka-ui
```

### Service URLs

Once setup is complete, access the services at:

* **Kafka**: `localhost:9092`
* **Vault**: `http://localhost:8200`
* **Kafka UI** (web interface): `http://localhost:8080`

### Environment Variables

The setup script automatically exports these variables. If you need them in new terminal sessions:

```bash
export VAULT_ADDR="http://localhost:8200"
export VAULT_TOKEN="dev-only-token"

# If using Vault Enterprise with namespaces:
export VAULT_NAMESPACE="admin"
```

---

## Local Demo Cases

### Demo 1 - Playload is visible to Kafka admin

This demonstrates that without encryption, anyone with Kafka admin access can read the message content.

**Steps:**

1. Open Kafka UI at `http://localhost:8080`
2. Navigate to Topics → `purchases` → Messages
3. In a terminal, run the producer:
```bash
python3 producer.py
```
4. Watch the messages appear in Kafka UI - you can see all the PII/PCI data in plaintext!

`★ Insight ─────────────────────────────────────`
**What's happening:**
- The producer generates fake purchase data with names, addresses, and credit card numbers
- Messages are sent to the `purchases` topic in plaintext
- Anyone with Kafka admin access can read this sensitive data
- This represents the risk of data leakage in cloud or SaaS Kafka environments
`─────────────────────────────────────────────────`

### Demo 2 - Per-field encryption with Vault

This demonstrates how Vault can encrypt sensitive fields individually:
- **Addresses** are encrypted using Vault Transit (AES-256-GCM)
- **Credit cards** are encrypted using Vault Transform FPE (preserves format)

**Steps:**

1. **Start the encryptor** (consumes from `purchases`, encrypts, produces to `purchases_encrypted`):
```bash
python3 encryptor.py
```

2. **Start the consumer** (consumes from `purchases_encrypted`, decrypts, displays):
```bash
python3 consumer_from_encrypted.py
```

3. **In another terminal, generate traffic**:
```bash
python3 producer.py
```

4. **Observe in Kafka UI**:
   - Navigate to Topics → `purchases_encrypted` → Messages
   - You'll see encrypted ciphertext for addresses
   - Credit cards are encrypted but maintain the same format (16 digits)

5. **Key rotation demonstration**:
```bash
# In Vault, rotate the transit key:
docker exec vault vault write -f transit/keys/transit/rotate

# Generate new messages - they'll use the new key version:
python3 producer.py

# The consumer can still decrypt both old and new messages!
```

`★ Insight ─────────────────────────────────────`
**Key concepts demonstrated:**
- **Transit Secrets Engine**: General-purpose encryption as a service
- **Transform Secrets Engine**: Format-preserving encryption (FPE) maintains data format
- **Key Versioning**: Vault automatically tracks key versions, enabling seamless key rotation
- **Per-field Encryption**: Only sensitive fields are encrypted, maintaining queryability on other fields
`─────────────────────────────────────────────────`

### Demo 3 - Large payload with DEK

For large files, sending all data to Vault for encryption is inefficient. Instead, we:
1. Generate a single-use Data Encryption Key (DEK) in Vault
2. Encrypt the DEK with Vault's master key
3. Encrypt the large file locally using the DEK
4. Send both the encrypted file and encrypted DEK to Kafka

**Steps:**

1. **Prepare test files**:
```bash
# Copy some files to the source directory
cp test_file.txt source/
cp large-set-of-info.json source/
```

2. **Start the consumer** (consumes, decrypts DEK from Vault, decrypts file, saves to `destination/`):
```bash
python3 consumer_file_transfer.py
```

3. **Start the producer** (scans `source/`, generates DEK, encrypts locally, sends to Kafka):
```bash
python3 producer_file_transfer.py
```

4. **Verify the result**:
```bash
ls -la destination/
# You should see the decrypted files appear
```

5. **In Kafka UI**, observe:
   - Topic: `purchases_large_encrypted`
   - Message body: Encrypted file content
   - HTTP Headers: Encrypted DEK and filename

`★ Insight ─────────────────────────────────────`
**Why this approach?**
- **Performance**: Large files are encrypted/decrypted locally, reducing Vault load
- **Security**: Each file gets a unique DEK, limiting blast radius if compromised
- **Scalability**: Vault only handles small DEK operations, not large file operations
- **Envelope Encryption**: Industry-standard pattern used by AWS KMS, GCP KMS, Azure Key Vault
`─────────────────────────────────────────────────`

---

## Troubleshooting

### Services won't start

**Issue**: Ports already in use
```bash
# Check what's using the ports
lsof -i :9092  # Kafka
lsof -i :8200  # Vault
lsof -i :8080  # Kafka UI

# Stop the conflicting services or change ports in docker-compose.yml
```

### Vault initialization fails

**Issue**: Vault token not set
```bash
# Set the dev token explicitly
export VAULT_TOKEN="dev-only-token"
./scripts/init-vault.sh
```

### Kafka connection errors

**Issue**: Topics not created
```bash
# Manually create topics
./scripts/create-topics.sh
```

### Python scripts can't connect

**Issue**: Wrong configuration file
```bash
# Ensure you're using the local config
cp getting_started.local.ini getting_started.ini
```

### Clean restart

If something is really broken:
```bash
# Stop everything and remove all volumes
./teardown.sh
# When prompted, choose 'y' to remove volumes

# Start fresh
./setup.sh
```

---

## Stopping the Demo

When you're done:

```bash
./teardown.sh
```

This stops all containers. You'll be prompted whether to remove volumes (deletes all data).

---

## Confluent Cloud Setup (Original)

> ⚠️ **Note**: This is the original setup method requiring a Confluent Cloud account. For most users, the **Local Demo** above is recommended.

### Pre-requisites

* Vault Enterprise with ADP license
* Confluent Cloud account (free tier available for developers)

### Setup Confluent Cloud

1. Go to [confluent.cloud](https://confluent.cloud/) and sign-up for a free account
2. During registration, select **"developer"** as your job role
   - Developers get free trial without expiry (limited to 1 Kafka cluster)

3. Once logged in, create a **Cloud API key** with global access

4. Set up environment variables:
```bash
export CONFLUENT_CLOUD_API_SECRET=<your secret>
export CONFLUENT_CLOUD_API_KEY=<your key>
```

5. Navigate to the terraform directory and apply the configuration:
```bash
cd terraform/confluent_terraform
terraform init
terraform plan
terraform apply
```

The Terraform code will create:
- Confluent Environment: `Development`
- Kafka Cluster: `basic__demo_kafka_cluster` (Basic tier, GCP, Australia region)
- Topics: `purchases`, `purchases_encrypted`, `purchases_large_encrypted`
- Service Account: `app-manager` with cluster admin role
- API Keys for authentication

6. After Terraform completes, note the following outputs:
   - **Cluster bootstrap servers** - from `confluent_kafka_cluster.demo`
   - **API key and secret** - from `confluent_api_key.app-manager-kafka-api-key`
   - You'll need these for `getting_started.ini`

### Setup Python Environment

[Install python3, pip and virtual environment manager](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/), then setup all dependencies:

```bash
python3 -m pip install -r requirements.txt
```

### Setup Configuration

1. Rename `getting_started.ini.orig` to `getting_started.ini`:
```bash
mv getting_started.ini.orig getting_started.ini
```

2. Edit `getting_started.ini` and update:
   - `bootstrap.servers` - Your Confluent Cloud cluster URL
   - `sasl.username` - Your Kafka API key
   - `sasl.password` - Your Kafka API secret

Example:
```ini
[default]
bootstrap.servers=pkc-4vndj.australia-southeast1.gcp.confluent.cloud:9092
security.protocol=SASL_SSL
sasl.mechanisms=PLAIN
sasl.username=PVL2XNIV6VWPJA3C
sasl.password=your-secret-here
```

---

## Confluent Cloud Demo Cases

### Demo 1 - Confluent admin can see messages on topic

Login to (confluent.cloud), open the 'purchase' topic, and click 'messages' tab to view messages on the topic.

Run producer.py in a terminal to generate some traffic, message should appear in the browser. This is to show that the contents of the payload is visible to admins.

`python3 producer.py`

### Demo 2 - Content can be encrypted

* Open the 'purchases_encrypted' topic and select 'messages' tab to observ messages.
In confluent cloud this is under > Environments > Developement > BASIC_DEMO_KAFKA_CLUSTER

* setup VAULT_ADDR and VAULT_TOKEN

```bash
export VAULT_ADDR="YOUR VAULT ADDRESS"
export VAULT_TOKEN="<YOUR VAULT TOKEN>"
```

* Run encryptor.py in a terminal `python3 encryptor.py` to consume messages from 'purchases' topic, encrypt, then send to 'purchases_encrypted' topic. Encrypted messages should apprear in the browser. This is to show that Vault can be used to do per-field encryption.

* Login to Vault, and rotate the transit encryption key.

Run producer.py in another terminal and observe that the encrypted messages would use the new version automatically.

Run consumer_from_encrypted.py in another terminal and observe that it can consume messages, decrypt, then print to the terminal. You would observe even though the encrypted messages were encrypted by two different versions, the consumer can still decrypt without difficulty.

You would also observe that the credit card numbers have been encrypted while preserving their formats. This enables complex logic between different topics.

### Demo 3 - Large payload

In the last two demo cases, all payloads are sent to Vault for both encryption and decryption operations. In the case of large payloads, this is not nessisarily the best way - large payloads increases network traffic and cause delays between producer and consumers, this also creates lots of CPU intensive operations on Vault nodes, putting presure on the centralised Vault platform.

Doing encryption/decryption operations at the application node using Data Encryption Key generated by Vault can avoid expensive network and CPU operations. To ensure security, every operation will have a new DEK, which is also encrypted/transfered with the encrypted payload, only client with right authentication/authorization is able to decrypt the DEK, then use it to decrypt the payload.

Open 'purchases_large_encrypted' topic and observ messages.

Run consumer_file_transfer.py from one terminal.

Create two folders with name 'source' and 'destination', then copy some files into source directory.

Run producer_file_transfer.py to scan files in source folder, generate one use only DEK, encryupt the file contents locally, then send to 'purchases_large_encrypted' topic.

The consumer will consume the message, get encrypted DEK from http header, call vault to decrypt the DEK, then decrypt the file contents locally, then save it into destination folder.

In the browser, you should be able to see encrypted messages, encrypted DEK as http header as well as the filename as http header.

## Beyond Kafka

Kafka is one of the most popular streaming platform, but it is not the only one. The concept demostrated here is applicable to any streaming platform, including [AWS Kinesis](https://aws.amazon.com/kinesis/), [AWS SQS](https://aws.amazon.com/sqs/), [AWS SNS](https://aws.amazon.com/sns/), [Google Cloud Pub/Sub](https://cloud.google.com/pubsub), [Microsoft Azure Event Hubs](https://azure.microsoft.com/en-us/products/event-hubs/) as well as  [Apache Spark Streaming](https://www.databricks.com/glossary/what-is-spark-streaming).
