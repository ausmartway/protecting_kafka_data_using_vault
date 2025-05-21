#!/usr/bin/env python

import sys
import os
import json
import base64
import time
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Producer
import hvac
import urllib3
from Crypto.Cipher import AES

def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(description='Kafka Producer for encrypted file transfer')
    parser.add_argument('--config_file', type=FileType('r'), default='getting_started.ini',
                        help='Configuration file path (default: getting_started.ini)')
    return parser.parse_args()

def load_config(config_file):
    """Load configuration from file."""
    config_parser = ConfigParser()
    config_parser.read_file(config_file)
    
    # Base configuration
    config = dict(config_parser['default'])
    
    # Demo-specific configuration
    demo_config = dict(config_parser['large_payload'])
    
    return config, demo_config

def setup_vault_client():
    """Set up and authenticate with Vault."""
    # Disable TLS verification warnings
    urllib3.disable_warnings()
    
    # Check for required environment variables
    required_env_vars = ['VAULT_ADDR', 'VAULT_TOKEN', 'VAULT_NAMESPACE']
    missing_vars = [var for var in required_env_vars if var not in os.environ]
    
    if missing_vars:
        print(f"ERROR: Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables before running the script.")
        sys.exit(1)
    
    # Create a Vault client object and authenticate
    try:
        client = hvac.Client(
            url=os.environ['VAULT_ADDR'],
            token=os.environ['VAULT_TOKEN'],
            namespace=os.environ['VAULT_NAMESPACE'],
            verify=False
        )
        
        if not client.is_authenticated():
            print("ERROR: Failed to authenticate with Vault")
            sys.exit(1)
            
        print(f"Successfully authenticated with Vault at {os.environ['VAULT_ADDR']}")
        return client
    except Exception as e:
        print(f"ERROR: Failed to connect to Vault: {e}")
        sys.exit(1)

def get_encryption_key(vault_client):
    """Get a Data Encryption Key from Vault's transit secrets engine."""
    try:
        gen_key_response = vault_client.secrets.transit.generate_data_key(
            name='transit',
            key_type='plaintext',
        )
        return gen_key_response['data']['ciphertext'], gen_key_response['data']['plaintext']
    except Exception as e:
        print(f"ERROR: Failed to generate data key: {e}")
        sys.exit(1)

def get_nonce(vault_client, n_bytes=32):
    """Get a random nonce from Vault."""
    try:
        gen_bytes_response = vault_client.secrets.transit.generate_random_bytes(n_bytes=n_bytes)
        return gen_bytes_response['data']['random_bytes']
    except Exception as e:
        print(f"ERROR: Failed to generate nonce: {e}")
        sys.exit(1)

def encrypt_file(file_contents, plaintext_key, nonce):
    """Encrypt file contents using AES-GCM."""
    try:
        # Convert base64 key and nonce to bytes
        key_bytes = base64.b64decode(plaintext_key)
        nonce_bytes = base64.b64decode(nonce)
        
        # Encode file contents to base64
        file_contents_base64 = base64.b64encode(file_contents)
        
        # Create AES encryptor and encrypt
        encryptor = AES.new(key_bytes, AES.MODE_GCM, nonce_bytes)
        encrypted_contents, tag = encryptor.encrypt_and_digest(file_contents_base64)
        
        return encrypted_contents, tag
    except Exception as e:
        print(f"ERROR: Failed to encrypt file: {e}")
        return None, None

def delivery_callback(err, msg):
    """Callback function for message delivery reports."""
    if err:
        print(f'ERROR: Message failed delivery: {err}')
    else:
        filename = "unknown"
        if msg.headers():  # Check if headers exist
            for header in msg.headers():
                if header[0] == 'X-filename':
                    filename = header[1].decode('utf-8')
                    break
        
        print(f"File '{filename}' delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def main():
    """Main function to run the producer."""
    # Parse arguments and load configuration
    args = parse_args()
    config, demo_config = load_config(args.config_file)
    
    # Set up Vault client
    vault_client = setup_vault_client()
    
    # Create Kafka producer
    producer = Producer(config)
    
    # Get topic from configuration
    topic = demo_config['topic']
    
    # Define the path of the directory that contains the source files
    source_dir = demo_config['sourcedir']
    if not source_dir.endswith('/'):
        source_dir += '/'
    
    # Check if source directory exists
    if not os.path.isdir(source_dir):
        print(f"ERROR: Source directory '{source_dir}' does not exist")
        sys.exit(1)
    
    # Get list of files
    try:
        files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    except Exception as e:
        print(f"ERROR: Failed to list files in directory '{source_dir}': {e}")
        sys.exit(1)
    
    if not files:
        print(f"WARNING: No files found in directory '{source_dir}'")
        sys.exit(0)
    
    print(f"Found {len(files)} files to process in '{source_dir}'")
    
    # Process each file
    files_processed = 0
    files_failed = 0
    
    for filename in files:
        file_path = os.path.join(source_dir, filename)
        print(f"Processing file: {filename}")
        
        try:
            # Read file contents
            with open(file_path, 'rb') as f:
                file_contents = f.read()
            
            # Get encryption key and nonce from Vault
            ciphertext_key, plaintext_key = get_encryption_key(vault_client)
            nonce = get_nonce(vault_client)
            
            print(f"Generated encryption key and nonce for file: {filename}")
            
            # Encrypt file contents
            encrypted_contents, tag = encrypt_file(file_contents, plaintext_key, nonce)
            
            if encrypted_contents is None or tag is None:
                print(f"ERROR: Failed to encrypt file: {filename}")
                files_failed += 1
                continue
            
            # Create JSON payload
            data = json.dumps({
                'ciphertext': encrypted_contents.hex(),
                'tag': tag.hex(),
                'nonce': nonce,
            })
            
            # Create headers
            headers = [
                ('X-encryptionkey', ciphertext_key),
                ('X-filename', filename),
            ]
            
            # Produce message to Kafka
            producer.produce(
                topic=topic,
                value=data.encode('utf-8'),
                headers=headers,
                callback=delivery_callback
            )
            
            # Trigger delivery callbacks
            producer.poll(0)
            
            files_processed += 1
            
        except Exception as e:
            print(f"ERROR: Failed to process file '{filename}': {e}")
            files_failed += 1
    
    # Flush remaining messages
    print(f"Processed {files_processed} files. Flushing remaining messages...")
    remaining = producer.flush(10000)
    
    if remaining > 0:
        print(f"WARNING: {remaining} messages were not delivered")
    
    print(f"File transfer complete: {files_processed} files processed, {files_failed} failed")

if __name__ == '__main__':
    main()
