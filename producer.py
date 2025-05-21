#!/usr/bin/env python

import sys
import random
import json
import time
import threading
import termios
import fcntl
import os
from random import choice
from argparse import ArgumentParser, FileType
from configparser import ConfigParser
from confluent_kafka import Producer

def delivery_report(err, msg):
    """Callback function for message delivery reports."""
    if err is not None:
        print(f"Message delivery failed: {err}")
    # else:
        # print(f"Message delivered to {msg.topic()} [{msg.partition()}] at offset {msg.offset()}")

def parse_args():
    """Parse command line arguments."""
    parser = ArgumentParser(description='Kafka Producer for PII/PCI data')
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
    demo_config = dict(config_parser['plaintext-msg-demo'])
    
    return config, demo_config

def load_addresses(filename="fakeaddress.txt"):
    """Load addresses from file."""
    try:
        with open(filename, "r") as file:
            return [line.strip() for line in file.readlines()]
    except FileNotFoundError:
        print(f"Error: Address file '{filename}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading addresses: {e}")
        sys.exit(1)

def generate_pii_pci_data(user_ids, credit_cards, addresses):
    """Generate a random PII/PCI data record."""
    return {
        "Name": choice(user_ids),
        "Address": choice(addresses),
        "credit_card": choice(credit_cards)
    }

def setup_keyboard_listener():
    """Set up non-blocking keyboard input."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        # Set terminal to raw mode
        new_settings = termios.tcgetattr(fd)
        new_settings[3] = new_settings[3] & ~(termios.ECHO | termios.ICANON)  # lflags
        termios.tcsetattr(fd, termios.TCSANOW, new_settings)
        
        # Set non-blocking
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
    except Exception as e:
        print(f"Error setting up keyboard listener: {e}")
        termios.tcsetattr(fd, termios.TCSANOW, old_settings)
        return None, None
    
    return fd, old_settings

def check_for_space_key(fd):
    """Check if space key was pressed."""
    try:
        c = sys.stdin.read(1)
        return c == ' '
    except:
        return False

def restore_terminal(fd, old_settings):
    """Restore terminal settings."""
    if fd is not None and old_settings is not None:
        termios.tcsetattr(fd, termios.TCSANOW, old_settings)

if __name__ == '__main__':
    # Parse arguments and load configuration
    args = parse_args()
    config, demo_config = load_config(args.config_file)
    
    # Create Producer instance
    producer = Producer(config)
    
    # Load data sources
    addresses = load_addresses()
    
    # User IDs and credit card numbers
    user_ids = ["Richard Dickson", "Caroline Orozco", "Jill Sanchez", "John Barry", "Mikayla Shaw", 
                "Sandra Fuller", "Jesse Santiago", "Jimmy Hess", "Glenda Garcia", "Robert Snyder", 
                "Lindsay Thompson", "Heather Davis", "William Meyer", "Michael Stevenson", "Meagan Clark", 
                "John Perkins", "Nicole Anderson", "Angela Gould", "Diana Hart", "Joseph Mercado", 
                "Andrew Cannon", "James Watkins", "Erica Butler MD", "Trevor Peterson", "Ashley Miranda", 
                "David Morris", "Daniel Love", "Kayla Matthews", "Timothy Robinson", "Kelly Torres", 
                "Tara Day", "Gerald Smith", "Daniel Shields", "Melissa Hester", "Carrie Clark", 
                "Jose Ellison", "Angela Nelson", "Norma Love", "Jennifer Mendoza", "Carolyn Cooper", 
                "Lucas Pham", "Jillian May", "Patricia Blackburn", "Kathy Johnson", "Blake Martin", 
                "Tracy Murphy", "Maxwell Johnson", "Billy Carrillo", "Kathy Best", "Christopher Mayo", 
                "Sarah Fleming", "Nicole Dennis", "Javier Ward", "Lindsey Graves", "Eric Jones", 
                "John Gregory", "Jerry Wang", "Eric Case", "Mark Brock", "Logan Garrett", 
                "Jessica Smith", "Joseph Medina", "Thomas Booth", "Kenneth Adams", "Dr. Amanda Martinez MD", 
                "John Rich", "Andrea Skinner", "Shannon King", "Dustin Randall", "William Cross", 
                "Cory Allen", "Lindsey Harper", "John White", "Larry Norman", "Tracy Dawson", 
                "John Nelson", "Monique Vasquez", "Elizabeth Bright", "Phillip Eaton", "Stacey Mcfarland", 
                "Kelly Carpenter", "Gabrielle Hayes", "Deanna Gonzalez", "Amanda Roberts", "Sheri Young", 
                "Felicia Pacheco", "Teresa Reyes", "Curtis Peterson", "Keith Peterson", "Wendy Richards", 
                "Sara Chen", "Dr. Joshua Chavez", "Todd Ferguson", "Brandon Hughes", "Derrick Burgess", 
                "Holly Curry", "Bryce Brown", "Sara Morales MD", "James Smith"]
    
    credit_cards = ["2399-7885-4549-9944", "2603-8821-3929-1023", "2668-7464-1639-3863", "2541-1326-3711-3435", 
                    "2373-8263-4712-8822", "2665-1310-5188-7904", "5222-6537-8170-3886", "2505-8298-3374-6991", 
                    "2393-1978-6395-1948", "2393-8455-1148-1425", "2432-3419-5575-6509", "2705-2363-7925-7680", 
                    "2464-5363-8216-8902", "2462-4588-2529-5386", "2626-2841-3140-6902", "2492-1429-0645-0631", 
                    "2454-1441-5903-7301", "2599-2971-7270-9763", "2527-0168-6618-9265", "2260-7189-6026-5716", 
                    "2464-9457-7877-2203", "2362-8273-2124-7045", "2405-3162-4021-0945", "2436-6127-9115-5965", 
                    "2640-9860-2436-4830", "2416-4525-4527-9702", "2539-3874-5457-7070", "2441-1661-1297-2031", 
                    "2694-6619-9714-5004", "2251-0981-1381-1570", "2438-5482-4147-8052", "2693-0311-0643-8032", 
                    "2574-7084-8989-1879", "2360-8714-5635-7775", "2574-6511-9133-1059", "2590-7478-8914-3879", 
                    "2671-0652-4779-1095", "2408-1792-3579-8481", "2459-3350-8507-2983", "2686-9806-1372-2735", 
                    "2399-3387-3719-7342", "2672-6916-2910-6831", "2458-7109-9722-1921", "2412-7203-0751-2005", 
                    "2634-2853-1541-3648", "2362-2302-6347-0305", "2622-6511-4569-2350", "2639-2964-8242-2549", 
                    "2564-7187-4204-9282", "2592-5744-1423-2979", "2234-8410-9294-4843", "2648-4745-3157-7667", 
                    "2416-4910-8698-6028", "2712-2691-4482-6043", "2497-5467-0530-7773", "2420-8224-8390-4020", 
                    "2585-5525-7228-2365", "2709-3145-4021-6863", "2681-7316-3621-7541", "2398-4911-4001-0627", 
                    "2384-2652-7223-1037", "2242-8515-9188-6726", "2477-2536-4029-4687", "2399-6493-6205-0055", 
                    "2437-2861-1358-7087", "2696-3731-1765-4661", "2600-3610-3174-4135", "2714-0577-7412-8972", 
                    "2269-9643-7575-4156", "2518-5270-9025-6507", "2651-1023-4768-0151", "2640-2511-8161-9777", 
                    "2710-0916-9722-3481", "2495-9564-5420-6245", "2390-2271-5351-7902", "2465-1307-4507-3600", 
                    "2330-9627-9279-3539", "2616-7245-9437-3240", "2530-0452-1519-4028", "2580-7638-4485-5111", 
                    "2381-4313-6951-2498", "2255-5837-8305-9770", "2338-6517-8736-4024", "2667-0204-5064-6037", 
                    "2270-3688-4923-4851", "2574-2856-6194-2051", "2516-2848-6785-9087", "2720-6287-3568-2364", 
                    "2692-1798-6350-8702", "2549-8272-0117-4539", "2661-7576-1094-1537", "2548-8070-9896-2452", 
                    "2513-9683-1022-9681", "2678-0715-1540-0271", "2231-3446-0418-8952", "2314-9558-7881-8808", 
                    "2602-7957-5931-6089", "2683-1391-7887-0321", "2549-6029-8640-5873"]
    
    # Set up producer parameters
    topic = demo_config['topic']
    num_messages = int(demo_config['number_of_msg'])
    sleep_time = int(demo_config['sleep_ms']) / 1000
    
    # Set random seed for reproducibility if needed
    random.seed()
    
    # Set up keyboard listener
    fd, old_settings = setup_keyboard_listener()
    
    # Produce messages
    print(f"Producing {num_messages} messages to topic '{topic}'...")
    print("Press SPACE to pause/resume message production")
    
    paused = False
    message_count = 0
    
    try:
        while message_count < num_messages:
            # Check for space key press
            if fd is not None and check_for_space_key(fd):
                paused = not paused
                if paused:
                    print("\n*** Message production PAUSED. Press SPACE to resume ***")
                else:
                    print("\n*** Message production RESUMED ***")
            
            # Skip message production if paused
            if paused:
                time.sleep(0.1)  # Short sleep to prevent CPU hogging
                continue
                
            # Generate data
            data = generate_pii_pci_data(user_ids, credit_cards, addresses)
            
            # Convert to JSON
            json_data = json.dumps(data)
            
            # Print data being sent
            print(json.dumps(data,indent=2))
            
            # Produce message
            producer.produce(
                topic=topic,
                value=json_data,
                callback=delivery_report
            )
            
            # Trigger any available delivery callbacks
            producer.poll(0)
            
            # Increment message counter
            message_count += 1
            
            # Sleep between messages
            time.sleep(sleep_time)
            
        print(f"All {num_messages} messages produced. Flushing remaining messages...")
        
        # Block until the messages are sent
        remaining = producer.flush(10)
        
        if remaining > 0:
            print(f"Warning: {remaining} messages were not delivered")
        else:
            print("All messages successfully delivered")
            
    except KeyboardInterrupt:
        print("\nProducer interrupted by user")
    except Exception as e:
        print(f"Error producing messages: {e}")
    finally:
        # Restore terminal settings
        restore_terminal(fd, old_settings)
        
        # Ensure all messages are delivered before exiting
        remaining = producer.flush(10)
        if remaining > 0:
            print(f"Warning: {remaining} messages were not delivered")
