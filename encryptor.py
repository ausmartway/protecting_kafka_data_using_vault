#!/usr/bin/env python

import sys
import os
import json
import base64
import signal
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Consumer, Producer, OFFSET_BEGINNING
import hvac
import urllib3

def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(description='Kafka message encryptor using HashiCorp Vault')
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

def delivery_callback(err, msg):
    """Callback function for message delivery reports."""
    if err:
        print(f'ERROR: Message failed delivery: {err}')
    else:
        json_payload = json.loads(msg.value().decode('utf-8'))
        print(json.dumps(json_payload, indent=2))

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

def encrypt_credit_card(client, credit_card):
    """Encrypt credit card using Vault's transform secrets engine."""
    try:
        response = client.secrets.transform.encode(
            role_name="payments",
            value=credit_card,
            transformation="creditcard"
        )
        return response['data']['encoded_value']
    except Exception as e:
        print(f"ERROR: Failed to encrypt credit card: {e}")
        return f"ENCRYPTION_ERROR: {str(e)}"

def encrypt_address(client, address):
    """Encrypt address using Vault's transit secrets engine."""
    try:
        # Convert address to base64
        address_bytes = address.encode('ascii')
        address_base64 = base64.b64encode(address_bytes)
        
        # Encrypt using transit engine
        response = client.secrets.transit.encrypt_data(
            name='transit',
            plaintext=str(address_base64, "utf-8"),
        )
        return response['data']['ciphertext']
    except Exception as e:
        print(f"ERROR: Failed to encrypt address: {e}")
        return f"ENCRYPTION_ERROR: {str(e)}"

def process_message(msg, client, producer, target_topic):
    """Process a single message, encrypt sensitive fields, and produce to target topic."""
    try:
        # Parse original payload
        original_payload = json.loads(msg.value().decode('utf-8'))
        
        # Encrypt sensitive fields
        encrypted_credit_card = encrypt_credit_card(client, original_payload["credit_card"])
        encrypted_address = encrypt_address(client, original_payload["Address"])
        
        # Create encrypted payload
        encrypted_payload = {
            "Name": original_payload["Name"],
            "Address": encrypted_address,
            "credit_card": encrypted_credit_card
        }
        
        # Convert to JSON and produce to target topic
        json_payload = json.dumps(encrypted_payload)
        producer.produce(target_topic, json_payload, callback=delivery_callback)
        producer.poll(0)  # Trigger delivery callbacks
        
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
    print("\nShutting down encryptor...")
    global running
    running = False

def main():
    """Main function to run the encryptor."""
    global args, running
    
    # Parse arguments and load configuration
    args = parse_args()
    config, demo_config = load_config(args.config_file)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Set up Vault client
    vault_client = setup_vault_client()
    
    # Create Kafka consumer and producer
    consumer = Consumer(config)
    producer = Producer(config)
    
    # Get topics from configuration
    source_topic = demo_config['sourcetopic']
    target_topic = demo_config['targettopic']
    
    # Subscribe to source topic
    consumer.subscribe([source_topic], on_assign=reset_offset)
    
    print(f"Encryptor started. Reading from '{source_topic}', writing to '{target_topic}'")
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
            success = process_message(msg, vault_client, producer, target_topic)
            
            if success:
                messages_processed += 1
            else:
                messages_failed += 1
                
            # # Print status every 10 messages
            # if (messages_processed + messages_failed) % 10 == 0:
            #     print(f"Status: {messages_processed} messages processed, {messages_failed} failed")
                
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}")
    finally:
        # Flush producer
        remaining = producer.flush(10)
        if remaining > 0:
            print(f"WARNING: {remaining} messages were not delivered")
            
        # Close consumer
        consumer.close()
        
        print(f"Encryptor stopped. Processed {messages_processed} messages, {messages_failed} failed")

if __name__ == '__main__':
    main()

