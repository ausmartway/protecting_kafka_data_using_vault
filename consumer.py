#!/usr/bin/env python

import sys
import signal
import json
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Consumer, OFFSET_BEGINNING, KafkaException

def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(description='Kafka Consumer')
    parser.add_argument('--config_file', type=FileType('r'), default='getting_started.ini',
                        help='Configuration file path (default: getting_started.ini)')
    parser.add_argument('--reset', action='store_true',
                        help='Reset consumer group offsets to beginning')
    return parser.parse_args()

def parse_config(config_file):
    """Parse configuration from file."""
    config_parser = ConfigParser()
    config_parser.read_file(config_file)
    
    # Base configuration
    config = dict(config_parser['default'])
    config.update(config_parser['consumer'])
    
    # Demo-specific configuration
    demo_config = dict(config_parser['plaintext-msg-demo'])
    
    return config, demo_config

def reset_offset(consumer, partitions):
    """Reset consumer offset to beginning if requested."""
    if args.reset:
        for p in partitions:
            p.offset = OFFSET_BEGINNING
        consumer.assign(partitions)
        print("Consumer offsets have been reset to beginning")

def handle_message(msg):
    """Process a Kafka message."""
    if msg is None:
        return False
    
    if msg.error():
        # Handle specific error types differently if needed
        print(f"ERROR: {msg.error()}")
        return True
    
    try:
        # Process the message
        value = msg.value().decode('utf-8')
        json_payload = json.loads(value)
        print(json.dumps(json_payload,indent=2))

    except Exception as e:
        print(f"Error processing message: {e}")
    
    return True

def shutdown_handler(signum, frame):
    """Handle graceful shutdown on signals."""
    print("\nShutting down consumer...")
    global running
    running = False

if __name__ == '__main__':
    # Parse arguments and configuration
    args = parse_args()
    config, demo_config = parse_config(args.config_file)
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Create Consumer instance
    consumer = Consumer(config)
    
    # Subscribe to topic
    topic = demo_config['topic']
    consumer.subscribe([topic], on_assign=reset_offset)
    
    # Poll for new messages from Kafka and process them
    running = True
    try:
        while running:
            msg = consumer.poll(1.0)
            if not handle_message(msg) and msg is None:
                print("Waiting for messages...")
    except KafkaException as e:
        print(f"Kafka error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    finally:
        # Leave group and commit final offsets
        print("Closing consumer and committing offsets...")
        consumer.close()
        print("Consumer closed successfully")
