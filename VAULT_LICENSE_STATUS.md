# Vault Enterprise License Status

## ⚠️ License Expired

The Vault Enterprise license provided has **expired**:
- **License Expiration**: 2024-04-01
- **Docker Image Build**: 2024-06-10
- **Result**: License is invalid for this Vault version

## Current Setup: Vault OSS

The demo is configured to use **Vault Open Source** which includes:

✅ **Transit Secrets Engine** - General-purpose encryption
✅ **Envelope Encryption** - DEK-based encryption for large files
✅ **Key Versioning** - Automatic key rotation support
✅ **API-based Encryption** - Encryption as a Service

❌ **Transform Secrets Engine** - Format-preserving encryption (FPE)
   - Requires Vault Enterprise with valid license
   - Used for credit card encryption in Demo 2

## What Works Now

### Demo 1: Plaintext Producer
```bash
python3 producer.py
```
Status: ✅ **Fully Working**

### Demo 3: Large File Transfer
```bash
cp test_file.txt source/
python3 consumer_file_transfer.py &
python3 producer_file_transfer.py
```
Status: ✅ **Fully Working** (Uses Transit only)

### Demo 2: Per-Field Encryption
```bash
python3 encryptor.py &      # Will fail on credit card FPE
python3 consumer_from_encrypted.py &
python3 producer.py
```
Status: ⚠️ **Partial** - Address encryption works, credit card FPE fails

## To Enable Full Enterprise Features

### Option 1: Get Current License
1. Visit https://portal.hashicorp.com
2. Download a Vault Enterprise license valid for 1.17.0
3. Replace `vault.hclic` with the new license
4. Run `./setup.sh`

### Option 2: Use Older Vault Image
Edit `docker-compose.yml`:
```yaml
vault:
  image: hashicorp/vault-enterprise:1.15.0-ent  # Built before 2024-04-01
```

## Running the Demo Now

The setup is ready with Vault OSS:

```bash
./setup.sh

# Test plaintext producer (Demo 1)
python3 producer.py

# Test large file transfer (Demo 3)
cp test_file.txt source/
python3 consumer_file_transfer.py &
python3 producer_file_transfer.py
```

## Summary

- **Current Configuration**: Vault OSS (no license needed)
- **Working Features**: Transit encryption, envelope encryption
- **Missing Features**: Transform FPE (credit card format-preserving encryption)
- **Recommendation**: Demo works for core encryption concepts with OSS
