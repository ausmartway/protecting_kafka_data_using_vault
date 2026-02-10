# Terraform Configuration Backup

## Overview

This document describes the original Terraform configuration for deploying this demo on Confluent Cloud. The configuration has been preserved in the `terraform/` directory but is no longer the recommended setup method.

## Original Architecture

The Terraform configuration in `terraform/confluent_terraform/` automated the provisioning of Confluent Cloud resources for the Kafka + Vault encryption demo.

### Resources Created

The Terraform configuration created the following Confluent Cloud resources:

#### 1. Confluent Environment
- **Name**: `Development`
- **Purpose**: Logical grouping for Confluent resources

#### 2. Kafka Cluster
- **Name**: `basic__demo_kafka_cluster`
- **Type**: Basic (single-zone)
- **Cloud Provider**: GCP
- **Region**: `australia-southeast1`
- **Tier**: Basic (suitable for development/testing)

#### 3. Service Account
- **Name**: `app-manager`
- **Description**: Service account to manage Kafka cluster
- **Permissions**: `CloudClusterAdmin` role on the cluster

#### 4. Kafka API Keys
- **Name**: `app-manager-kafka-api-key`
- **Owner**: `app-manager` service account
- **Purpose**: Authentication for Kafka operations
- **Scopes**: Cluster-level access

#### 5. Kafka Topics

Three topics were automatically created:

| Topic Name | Purpose | Partitions | Special Config |
|------------|---------|------------|----------------|
| `purchases` | Plaintext purchase data | 1 | None |
| `purchases_encrypted` | Per-field encrypted data | 1 | None |
| `purchases_large_encrypted` | Large payloads with DEK | 1 | `max.message.bytes=8388608` |

## Terraform Files

### `terraform/confluent_terraform/main.tf`
Main Terraform configuration defining:
- Provider configuration (Confluent provider v2.28.0)
- All resource definitions
- Dependencies between resources

### `terraform/confluent_terraform/output.tf`
Output definitions for:
- Cluster bootstrap servers
- API keys and secrets
- Resource IDs

### `terraform/confluent_terraform/terraform.tfstate`
Terraform state file (should NOT be committed to git)
- Contains current state of Confluent Cloud resources
- Includes sensitive data (API secrets)

### `terraform/confluent_terraform/.terraform.lock.hcl`
Dependency lock file for Terraform providers

## Migration to Local Docker Compose

### Why the Change?

The Terraform/Confluent Cloud approach had several drawbacks:

1. **External Account Required**: Users needed to sign up for Confluent Cloud
2. **Cost**: Free tier limited; potential costs if limits exceeded
3. **Internet Dependency**: Required internet connectivity
4. **Complex Setup**: Multiple steps (account, API keys, Terraform)
5. **Data Privacy**: Demo data sent to external service
6. **Network Latency**: Additional latency for cloud services

The new **Docker Compose** approach addresses all these issues:
- ✅ Runs entirely locally
- ✅ No external accounts
- ✅ Works offline
- ✅ Simple one-command setup
- ✅ Data stays on your machine
- ✅ Faster (no network latency)

### What's Changed

| Component | Confluent Cloud (Old) | Local Docker (New) |
|-----------|----------------------|-------------------|
| Kafka | Confluent Cloud SaaS | Local container |
| Zookeeper | Managed by Confluent | Local container |
| Vault | External or self-managed | Local container |
| Web UI | Confluent Cloud Console | Kafka UI (local) |
| Setup | Terraform + Account | Single script |

### What's Preserved

All Python scripts remain **100% compatible** with both approaches:
- ✅ `producer.py`
- ✅ `consumer.py`
- ✅ `encryptor.py`
- ✅ `consumer_from_encrypted.py`
- ✅ `producer_file_transfer.py`
- ✅ `consumer_file_transfer.py`

The only difference is the `getting_started.ini` configuration file:
- **Local**: Uses `localhost:9092` (plaintext)
- **Confluent**: Uses cloud endpoint with SASL_SSL

## Restoring the Confluent Cloud Setup

If you need to restore the original Confluent Cloud setup:

### 1. Get Confluent Cloud Credentials

```bash
export CONFLUENT_CLOUD_API_KEY=<your-key>
export CONFLUENT_CLOUD_API_SECRET=<your-secret>
```

### 2. Apply Terraform Configuration

```bash
cd terraform/confluent_terraform
terraform init
terraform plan
terraform apply
```

### 3. Update `getting_started.ini`

Copy the outputs from Terraform to your configuration file:
- Bootstrap servers
- API key
- API secret

### 4. Run Python Scripts

All scripts work the same way with Confluent Cloud.

### 5. Clean Up (When Done)

To destroy Confluent Cloud resources:

```bash
cd terraform/confluent_terraform
terraform destroy
```

⚠️ **Important**: This will delete all Confluent Cloud resources created by Terraform.

## Terraform State Management

### State File Location

- **Location**: `terraform/confluent_terraform/terraform.tfstate`
- **Contains**: Resource IDs, API secrets, metadata
- **Security**: Should be in `.gitignore` (it is)

### State Backup

If you want to preserve the Confluent Cloud state:

```bash
# Backup current state
cp terraform/confluent_terraform/terraform.tfstate \
   terraform/confluent_terraform/terraform.tfstate.backup
```

### Remote State (Recommended for Production)

For team collaboration, use Terraform Cloud or remote backend:

```hcl
terraform {
  backend "remote" {
    organization = "your-org"
    workspaces {
      name = "kafka-vault-demo"
    }
  }
}
```

## Vault Configuration

The Confluent Cloud setup used external Vault instances. Vault configuration scripts remain the same:

- **Transit Secrets Engine**: `scripts/init-vault.sh`
- **Transform Secrets Engine**: `scripts/init-vault.sh`

These work with any Vault instance (local, cloud, or on-premises).

## Comparison Summary

| Aspect | Local Docker | Confluent Cloud |
|--------|--------------|-----------------|
| **Setup Time** | ~2 minutes | ~15 minutes |
| **Prerequisites** | Docker only | Confluent account, Terraform |
| **Cost** | Free | Free tier (limited) |
| **Network** | Local | Internet required |
| **Data Privacy** | On your machine | Cloud-hosted |
| **Maintenance** | Low | Low (managed) |
| **Use Case** | Development, demos | Production-like testing |

## Recommendation

For most users, especially those:
- Learning Kafka security patterns
- Demonstrating Vault encryption
- Developing locally
- Running demos/presentations

**Use the Local Docker Compose setup** (`./setup.sh`)

The Confluent Cloud setup remains available for:
- Production-like testing
- Multi-region demos
- Cloud-native architecture evaluation
- Cost comparison exercises

## Additional Resources

- [Confluent Terraform Provider](https://registry.terraform.io/providers/confluentinc/confluent/latest/docs)
- [Confluent Cloud Documentation](https://docs.confluent.io/cloud/current/)
- [Local Docker Setup Guide](../README.md#local-demo-setup-recommended)
