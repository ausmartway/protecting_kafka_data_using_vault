"""
Test configuration and fixtures for the Kafka Vault encryption project.
"""

import os
import sys
import json
import tempfile
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import pytest
import base64

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def vault_env_vars():
    """Provide Vault environment variables for testing."""
    os.environ.setdefault('VAULT_ADDR', 'http://localhost:8200')
    os.environ.setdefault('VAULT_TOKEN', 'test-token')
    os.environ.setdefault('VAULT_NAMESPACE', 'admin')
    return {
        'VAULT_ADDR': os.environ['VAULT_ADDR'],
        'VAULT_TOKEN': os.environ['VAULT_TOKEN'],
        'VAULT_NAMESPACE': os.environ['VAULT_NAMESPACE']
    }


@pytest.fixture
def sample_pci_data():
    """Provide sample PII/PCI data for testing."""
    return {
        "Name": "John Doe",
        "Address": "123 Main St, Sydney NSW 2000",
        "credit_card": "4532-1234-5678-9010"
    }


@pytest.fixture
def sample_pci_data_list():
    """Provide a list of sample PII/PCI data for testing."""
    return [
        {
            "Name": "Alice Smith",
            "Address": "456 Oak Ave, Melbourne VIC 3000",
            "credit_card": "5222-6537-8170-3886"
        },
        {
            "Name": "Bob Jones",
            "Address": "789 Pine Rd, Brisbane QLD 4000",
            "credit_card": "2399-7885-4549-9944"
        }
    ]


@pytest.fixture
def mock_vault_client():
    """Create a mock Vault client for testing."""
    mock_client = MagicMock()

    # Mock transit encryption/decryption
    mock_client.secrets.transit.encrypt_data.return_value = {
        'data': {
            'ciphertext': 'vault:v1:encrypted_base64_data'
        }
    }

    mock_client.secrets.transit.decrypt_data.return_value = {
        'data': {
            'plaintext': base64.b64encode(b'Sydney NSW 2000').decode('utf-8')
        }
    }

    # Mock generate data key
    mock_client.secrets.transit.generate_data_key.return_value = {
        'data': {
            'ciphertext': 'vault:v1:encrypted_dek',
            'plaintext': base64.b64encode(os.urandom(32)).decode('utf-8')
        }
    }

    # Mock generate random bytes
    mock_client.secrets.transit.generate_random_bytes.return_value = {
        'data': {
            'random_bytes': base64.b64encode(os.urandom(32)).decode('utf-8')
        }
    }

    # Mock transform encode/decode
    mock_client.secrets.transform.encode.return_value = {
        'data': {
            'encoded_value': '4532-XXXX-XXXX-XXXX'
        }
    }

    mock_client.secrets.transform.decode.return_value = {
        'data': {
            'decoded_value': '4532-1234-5678-9010'
        }
    }

    return mock_client


@pytest.fixture
def mock_kafka_producer():
    """Create a mock Kafka producer for testing."""
    producer = Mock()
    producer.produce = Mock()
    producer.poll = Mock()
    producer.flush = Mock()
    return producer


@pytest.fixture
def mock_kafka_consumer():
    """Create a mock Kafka consumer for testing."""
    consumer = Mock()

    # Mock message
    mock_msg = Mock()
    mock_msg.topic.return_value = 'test-topic'
    mock_msg.value.return_value = json.dumps({
        "Name": "Test User",
        "Address": "Test Address",
        "credit_card": "4532-1234-5678-9010"
    }).encode('utf-8')
    mock_msg.error.return_value = None
    mock_msg.headers.return_value = [
        ('X-encryptionkey', b'vault:v1:test_key'),
        ('X-filename', b'test.txt')
    ]

    consumer.poll.return_value = mock_msg
    consumer.subscribe = Mock()
    consumer.close = Mock()
    consumer.assign = Mock()

    return consumer


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file for testing."""
    config_content = """[default]
bootstrap.servers=localhost:9092
security.protocol=SASL_SSL
sasl.mechanisms=PLAIN
sasl.username=test-key
sasl.password=test-secret
message.max.bytes=8388608
enable.metrics.push=false

[consumer]
group.id=python_example_group_1
auto.offset.reset=earliest

[plaintext-msg-demo]
topic = purchases
number_of_msg = 10
sleep_ms = 100

[encryptor]
sourcetopic = purchases
targettopic = purchases_encrypted

[large_payload]
topic=purchases_large_encrypted
sourcedir = source
destinationdir=destination
"""

    with tempfile.NamedTemporaryFile(mode='w', suffix='.ini', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    yield temp_path

    # Cleanup
    os.unlink(temp_path)


@pytest.fixture
def temp_source_dir():
    """Create a temporary source directory with test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = os.path.join(temp_dir, 'source')
        os.makedirs(source_dir)

        # Create test files
        test_files = {
            'test1.txt': b'This is test file 1',
            'test2.txt': b'This is test file 2 with more content',
            'test3.json': b'{"key": "value", "number": 123}'
        }

        for filename, content in test_files.items():
            with open(os.path.join(source_dir, filename), 'wb') as f:
                f.write(content)

        yield source_dir


@pytest.fixture
def temp_dest_dir():
    """Create a temporary destination directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        dest_dir = os.path.join(temp_dir, 'destination')
        os.makedirs(dest_dir)
        yield dest_dir


@pytest.fixture
def sample_addresses():
    """Provide sample addresses for testing."""
    return [
        "123 Main St, Sydney NSW 2000",
        "456 Oak Ave, Melbourne VIC 3000",
        "789 Pine Rd, Brisbane QLD 4000",
        "321 Beach Rd, Perth WA 6000",
        "654 Mountain St, Adelaide SA 5000"
    ]


@pytest.fixture
def sample_credit_cards():
    """Provide sample credit card numbers for testing."""
    return [
        "4532-1234-5678-9010",
        "5222-6537-8170-3886",
        "2399-7885-4549-9944",
        "2603-8821-3929-1023",
        "2668-7464-1639-3863"
    ]


@pytest.fixture
def encrypted_payload():
    """Provide an encrypted payload for testing."""
    return {
        "Name": "John Doe",
        "Address": "vault:v1:encrypted_address_data",
        "credit_card": "4532-XXXX-XXXX-XXXX"
    }


@pytest.fixture
def large_encrypted_message():
    """Provide a large encrypted message for testing."""
    return {
        'ciphertext': 'a1b2c3d4e5f6',
        'tag': '1234567890abcdef',
        'nonce': base64.b64encode(os.urandom(32)).decode('utf-8')
    }
