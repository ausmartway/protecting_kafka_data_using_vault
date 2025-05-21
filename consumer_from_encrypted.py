#!/usr/bin/env python

import sys
import os
import json
import base64
import signal
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from textwrap import indent
from confluent_kafka import Consumer, OFFSET_BEGINNING, KafkaException
import hvac
import urllib3

def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(description='Kafka Consumer for encrypted messages')
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
    demo_config = dict(config_parser['encryptor'])
    
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

def decrypt_credit_card(client, encrypted_value):
    """Decrypt credit card using Vault's transform secrets engine."""
    try:
        response = client.secrets.transform.decode(
            role_name="payments",
            value=encrypted_value,
            transformation="creditcard"
        )
        return response['data']['decoded_value']
    except Exception as e:
        print(f"ERROR: Failed to decrypt credit card: {e}")
        return f"DECRYPTION_ERROR: {str(e)}"

def decrypt_address(client, encrypted_value):
    """Decrypt address using Vault's transit secrets engine."""
    try:
        # Decrypt using transit engine
        response = client.secrets.transit.decrypt_data(
            name='transit',
            ciphertext=encrypted_value,
        )
        
        # Decode from base64
        plaintext_base64 = str(response['data']['plaintext'])
        address_bytes = base64.b64decode(plaintext_base64)
        
        return address_bytes.decode("utf-8")
    except Exception as e:
        print(f"ERROR: Failed to decrypt address: {e}")
        return f"DECRYPTION_ERROR: {str(e)}"

def process_message(msg, client):
    """Process a single message, decrypt sensitive fields."""
    try:
        # Parse encrypted payload
        encrypted_payload = json.loads(msg.value().decode('utf-8'))
        
        # Decrypt sensitive fields
        decrypted_credit_card = decrypt_credit_card(client, encrypted_payload["credit_card"])
        decrypted_address = decrypt_address(client, encrypted_payload["Address"])
        
        # Create decrypted payload
        decrypted_payload = {
            "Name": encrypted_payload["Name"],
            "Address": decrypted_address,
            "credit_card": decrypted_credit_card
        }
        
        # Output decrypted payload
        print(json.dumps(decrypted_payload,indent=2))
        
        return True
    except json.JSONDecodeError:
        print(f"ERROR: Invalid JSON in message: {msg.value().decode('utf-8')[:100]}")
    except KeyError as e:
        print(f"ERROR: Missing required field in message: {e}")
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
    
    # Get topic from configuration
    topic = demo_config['targettopic']
    
    # Subscribe to topic
    consumer.subscribe([topic], on_assign=reset_offset)
    
    print(f"Consumer started. Reading from '{topic}'")
    print("Press Ctrl+C to exit")
    
    # Process messages
    running = True
    messages_processed = 0
    messages_failed = 0
    
    try:
        while running:
            msg = consumer.poll(1.0)
            
            if msg is None:
                # No message received
                continue
                
            if msg.error():
                print(f"ERROR: Consumer error: {msg.error()}")
                continue
                
            # Process message
            success = process_message(msg, vault_client)
            
            if success:
                messages_processed += 1
            else:
                messages_failed += 1
                
            # Print status every 10 messages
            if (messages_processed + messages_failed) % 10 == 0:
                print(f"Status: {messages_processed} messages processed, {messages_failed} failed")
                
    except KafkaException as e:
        print(f"ERROR: Kafka error: {e}")
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
    finally:
        # Close consumer
        consumer.close()
        
        print(f"Consumer stopped. Processed {messages_processed} messages, {messages_failed} failed")

if __name__ == '__main__':
    main()
