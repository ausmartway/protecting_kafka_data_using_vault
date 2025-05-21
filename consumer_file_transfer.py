#!/usr/bin/env python

import sys
import os
import json
import base64
import signal
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Consumer, OFFSET_BEGINNING, KafkaException
import hvac
import urllib3
from Crypto.Cipher import AES

def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(description='Kafka Consumer for encrypted file transfer')
    parser.add_argument('--config_file', type=FileType('r'), default='getting_started.ini',
                        help='Configuration file path (default: getting_started.ini)')
    parser.add_argument('--reset', action='store_true',
                        help='Reset consumer group offsets to beginning')
    return parser.parse_args()

def load_config(config_file):
    """Load configuration from file."""
    config_parser = ConfigParser()
    config_parser.read_file(config_file)
    
    # Base configuration
    config = dict(config_parser['default'])
    config.update(config_parser['consumer'])
    
    # Demo-specific configuration
    demo_config = dict(config_parser['large_payload'])
    
    return config, demo_config

def reset_offset(consumer, partitions):
    """Reset consumer offset to beginning if requested."""
    if args.reset:
        for p in partitions:
            p.offset = OFFSET_BEGINNING
        consumer.assign(partitions)
        print("Consumer offsets have been reset to beginning")

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

def decrypt_data_encryption_key(client, encrypted_key):
    """Decrypt the Data Encryption Key using Vault's transit secrets engine."""
    try:
        response = client.secrets.transit.decrypt_data(
            name='transit',
            ciphertext=encrypted_key
        )
        return response['data']['plaintext']
    except Exception as e:
        print(f"ERROR: Failed to decrypt Data Encryption Key: {e}")
        return None

def process_file_message(msg, client, dest_dir):
    """Process a file transfer message and save the decrypted file."""
    try:
        # Parse encrypted payload
        encrypted_payload = json.loads(msg.value().decode('utf-8'))
        
        # Extract headers
        headers = dict(msg.headers())
        
        # Get filename from headers
        filename = headers.get('X-filename')
        if not filename:
            print("ERROR: Missing filename header")
            return False
        
        filename = filename.decode('utf-8')
        
        # Get and decrypt the Data Encryption Key
        encrypted_key = headers.get('X-encryptionkey')
        if not encrypted_key:
            print("ERROR: Missing encryption key header")
            return False
        
        encrypted_key = encrypted_key.decode('utf-8')
        print(f"Processing file: {filename}")
        print(f"Data Encryption Key from header: {encrypted_key}")
        
        # Decrypt the Data Encryption Key
        plaintext_key = decrypt_data_encryption_key(client, encrypted_key)
        if not plaintext_key:
            return False
        
        print(f"Data Encryption Key decrypted successfully")
        
        # Get nonce from payload
        nonce = encrypted_payload.get('nonce')
        if not nonce:
            print("ERROR: Missing nonce in payload")
            return False
        
        # Get ciphertext and tag from payload
        ciphertext = encrypted_payload.get('ciphertext')
        tag = encrypted_payload.get('tag')
        if not ciphertext or not tag:
            print("ERROR: Missing ciphertext or tag in payload")
            return False
        
        # Decrypt the file contents
        try:
            # Create AES cipher
            cipher = AES.new(
                base64.b64decode(plaintext_key),
                AES.MODE_GCM,
                base64.b64decode(nonce)
            )
            
            # Decrypt and verify
            plaintext = cipher.decrypt_and_verify(
                bytes.fromhex(ciphertext),
                bytes.fromhex(tag)
            )
            
            # Decode base64 content
            file_content = base64.b64decode(plaintext)
            
            # Ensure destination directory exists
            os.makedirs(dest_dir, exist_ok=True)
            
            # Write to file
            output_path = os.path.join(dest_dir, f"received-{filename}")
            with open(output_path, 'wb') as f:
                f.write(file_content)
                
            print(f"File saved successfully: {output_path}")
            return True
            
        except Exception as e:
            print(f"ERROR: Failed to decrypt file: {e}")
            return False
            
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in message")
    except Exception as e:
        print(f"ERROR: Failed to process message: {e}")
    
    return False

def shutdown_handler(signum, frame):
    """Handle graceful shutdown on signals."""
    print("\nShutting down consumer...")
    global running
    running = False

def main():
    """Main function to run the consumer."""
    global args, running
    
    # Parse arguments and load configuration
    args = parse_args()
    config, demo_config = load_config(args.config_file)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Set up Vault client
    vault_client = setup_vault_client()
    
    # Create Kafka consumer
    consumer = Consumer(config)
    
    # Get topic and destination directory from configuration
    topic = demo_config['topic']
    dest_dir = demo_config['destinationdir']
    if not dest_dir.endswith('/'):
        dest_dir += '/'
    
    # Subscribe to topic
    consumer.subscribe([topic], on_assign=reset_offset)
    
    print(f"Consumer started. Reading from '{topic}', saving files to '{dest_dir}'")
    print("Press Ctrl+C to exit")
    
    # Process messages
    running = True
    files_processed = 0
    files_failed = 0
    
    try:
        while running:
            msg = consumer.poll(1.0)
            
            if msg is None:
                # No message received
                print("Waiting for messages...")
                continue
                
            if msg.error():
                print(f"ERROR: Consumer error: {msg.error()}")
                continue
                
            # Process message
            success = process_file_message(msg, vault_client, dest_dir)
            
            if success:
                files_processed += 1
                print(f"Files processed: {files_processed}")
            else:
                files_failed += 1
                print(f"Files failed: {files_failed}")
                
    except KafkaException as e:
        print(f"ERROR: Kafka error: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
    finally:
        # Close consumer
        consumer.close()
        
        print(f"Consumer stopped. Processed {files_processed} files, {files_failed} failed")

if __name__ == '__main__':
    main()
