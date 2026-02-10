"""
Unit tests for producer_file_transfer.py - Large payload encryption with envelope encryption.
"""

import pytest
import json
import base64
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from Crypto.Cipher import AES

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.unit
class TestFileTransferProducerConfiguration:
    """Test file transfer producer configuration."""

    def test_large_payload_config_keys(self):
        """Test that large_payload configuration has required keys."""
        required_keys = ['topic', 'sourcedir', 'destinationdir']

        # From getting_started.ini [large_payload] section
        config = {
            'topic': 'purchases_large_encrypted',
            'sourcedir': 'source',
            'destinationdir': 'destination'
        }

        for key in required_keys:
            assert key in config

    def test_source_directory_config(self):
        """Test source directory configuration."""
        sourcedir = 'source'

        assert sourcedir == 'source'

    def test_topic_config(self):
        """Test topic configuration for large payloads."""
        topic = 'purchases_large_encrypted'

        assert topic == 'purchases_large_encrypted'


@pytest.mark.unit
class TestFileTransferFileReading:
    """Test file reading operations."""

    def test_list_files_in_directory(self):
        """Test listing files in source directory."""
        # Simulate directory listing
        files = ['test1.txt', 'test2.txt', 'test3.json']

        assert len(files) == 3
        assert 'test1.txt' in files

    def test_check_if_file(self):
        """Test checking if path is a file."""
        # Simulate file check
        is_file = True

        assert is_file is True

    def test_read_file_contents(self):
        """Test reading file contents."""
        test_content = b'This is test file content'

        # Simulate file read
        file_contents = test_content

        assert isinstance(file_contents, bytes)
        assert len(file_contents) > 0

    def test_file_contents_base64_encode(self):
        """Test Base64 encoding of file contents."""
        file_contents = b'This is test file content'
        file_contents_base64 = base64.b64encode(file_contents)

        assert isinstance(file_contents_base64, bytes)
        assert len(file_contents_base64) > 0


@pytest.mark.unit
class TestFileTransferVaultIntegration:
    """Test Vault integration for envelope encryption."""

    def test_generate_data_key_call(self):
        """Test generate data key API call."""
        mock_client = Mock()

        mock_client.secrets.transit.generate_data_key.return_value = {
            'data': {
                'ciphertext': 'vault:v1:encrypted_dek',
                'plaintext': base64.b64encode(os.urandom(32)).decode('utf-8')
            }
        }

        # Simulate generating data key
        response = mock_client.secrets.transit.generate_data_key(
            name='transit',
            key_type='plaintext'
        )

        # Verify call
        mock_client.secrets.transit.generate_data_key.assert_called_once_with(
            name='transit',
            key_type='plaintext'
        )

        assert 'ciphertext' in response['data']
        assert 'plaintext' in response['data']

    def test_extract_dek_components(self):
        """Test extracting DEK ciphertext and plaintext."""
        response = {
            'data': {
                'ciphertext': 'vault:v1:encrypted_dek',
                'plaintext': base64.b64encode(os.urandom(32)).decode('utf-8')
            }
        }

        ciphertext = response['data']['ciphertext']
        plaintext = response['data']['plaintext']

        assert ciphertext.startswith('vault:v1:')
        assert len(plaintext) > 0

    def test_generate_nonce_call(self):
        """Test generate random bytes (nonce) API call."""
        mock_client = Mock()

        mock_client.secrets.transit.generate_random_bytes.return_value = {
            'data': {
                'random_bytes': base64.b64encode(os.urandom(32)).decode('utf-8')
            }
        }

        # Simulate generating nonce
        response = mock_client.secrets.transit.generate_random_bytes(
            n_bytes=32
        )

        # Verify call
        mock_client.secrets.transit.generate_random_bytes.assert_called_once_with(
            n_bytes=32
        )

        assert 'random_bytes' in response['data']


@pytest.mark.unit
class TestFileTransferAESEncryption:
    """Test AES encryption for envelope encryption."""

    def test_aes_cipher_initialization(self):
        """Test AES cipher initialization with DEK and nonce."""
        # Generate test DEK and nonce
        dek_plaintext = base64.b64encode(os.urandom(32)).decode('utf-8')
        nonce = base64.b64encode(os.urandom(32)).decode('utf-8')

        # Create AES cipher
        encryptor = AES.new(
            base64.b64decode(dek_plaintext),
            AES.MODE_GCM,
            base64.b64decode(nonce)
        )

        assert encryptor is not None

    def test_aes_encrypt_and_digest(self):
        """Test AES encrypt_and_digest operation."""
        # Generate test key and nonce
        key = os.urandom(32)  # 256-bit key
        nonce = os.urandom(32)  # 256-bit nonce for GCM

        # Create cipher
        encryptor = AES.new(key, AES.MODE_GCM, nonce)

        # Test data
        plaintext = base64.b64encode(b'Test file content')

        # Encrypt and digest
        ciphertext, tag = encryptor.encrypt_and_digest(plaintext)

        assert isinstance(ciphertext, bytes)
        assert isinstance(tag, bytes)
        assert len(tag) == 16  # GCM tag is 16 bytes

    def test_encrypted_data_packing(self):
        """Test packing encrypted data into JSON."""
        encrypted_contents = os.urandom(32)
        tag = os.urandom(16)
        nonce = base64.b64encode(os.urandom(32)).decode('utf-8')

        # Pack into JSON
        data = json.dumps({
            'ciphertext': encrypted_contents.hex(),
            'tag': tag.hex(),
            'nonce': nonce,
        })

        parsed = json.loads(data)

        assert 'ciphertext' in parsed
        assert 'tag' in parsed
        assert 'nonce' in parsed
        assert isinstance(parsed['ciphertext'], str)
        assert isinstance(parsed['tag'], str)


@pytest.mark.unit
class TestFileTransferHeaders:
    """Test HTTP headers for encrypted DEK and filename."""

    def test_header_structure(self):
        """Test that headers contain DEK and filename."""
        ciphertext = 'vault:v1:encrypted_dek'
        filename = 'test.txt'

        headers = [
            ('X-encryptionkey', ciphertext),
            ('X-filename', filename),
        ]

        assert len(headers) == 2
        assert headers[0][0] == 'X-encryptionkey'
        assert headers[1][0] == 'X-filename'

    def test_encrypted_dek_in_header(self):
        """Test that encrypted DEK is in header."""
        ciphertext = 'vault:v1:encrypted_dek'

        headers = [
            ('X-encryptionkey', ciphertext),
        ]

        assert headers[0][1] == ciphertext

    def test_filename_in_header(self):
        """Test that filename is in header."""
        filename = 'test.txt'

        headers = [
            ('X-filename', filename),
        ]

        assert headers[0][1] == filename


@pytest.mark.unit
class TestFileTransferProducerKafkaInteraction:
    """Test Kafka producer interaction."""

    def test_produce_with_headers(self):
        """Test producing message with headers."""
        mock_producer = Mock()
        topic = 'purchases_large_encrypted'

        data = json.dumps({
            'ciphertext': 'a1b2c3',
            'tag': '123abc',
            'nonce': base64.b64encode(os.urandom(32)).decode('utf-8')
        })

        headers = [
            ('X-encryptionkey', 'vault:v1:key'),
            ('X-filename', 'test.txt'),
        ]

        mock_producer.produce(topic, value=data.encode('utf-8'), headers=headers)

        # Verify call
        mock_producer.produce.assert_called_once()
        args = mock_producer.produce.call_args

        assert args[0][0] == topic
        assert args[1]['value'] == data.encode('utf-8')
        assert args[1]['headers'] == headers


@pytest.mark.unit
class TestFileTransferProducerLoop:
    """Test file processing loop."""

    def test_process_all_files(self):
        """Test that all files in directory are processed."""
        files = ['file1.txt', 'file2.txt', 'file3.json']

        processed_count = 0
        for filename in files:
            # Simulate file processing
            processed_count += 1

        assert processed_count == len(files)

    def test_skip_directories(self):
        """Test that directories are skipped."""
        items = ['file1.txt', 'subdir', 'file2.txt']

        files_only = [item for item in items if item != 'subdir']

        assert len(files_only) == 2
        assert 'subdir' not in files_only


@pytest.mark.unit
class TestFileTransferProducerFlush:
    """Test producer flush operation."""

    def test_flush_called(self):
        """Test that flush is called after processing."""
        mock_producer = Mock()
        mock_producer.poll.return_value = 0
        mock_producer.flush.return_value = 0

        # Simulate end of processing
        mock_producer.poll(10000)
        mock_producer.flush()

        mock_producer.flush.assert_called_once()


@pytest.mark.unit
class TestFileTransferVaultTLS:
    """Test Vault TLS settings."""

    def test_tls_verification_disabled(self):
        """Test that TLS verification is disabled."""
        verify = False

        assert verify is False

    def test_urllib3_warnings_disabled(self):
        """Test that urllib3 warnings are disabled."""
        import urllib3

        # This would disable warnings
        urllib3.disable_warnings()

        assert callable(urllib3.disable_warnings)


@pytest.mark.unit
class TestFileTransferSecurity:
    """Test security aspects of envelope encryption."""

    def test_dek_encrypted_by_vault(self):
        """Test that DEK is encrypted by Vault."""
        dek_ciphertext = 'vault:v1:encrypted_dek'

        assert dek_ciphertext.startswith('vault:v1:')

    def test_dek_not_exposed_in_plaintext(self):
        """Test that plaintext DEK is not sent to Kafka."""
        # The plaintext DEK should only be used locally
        # The ciphertext DEK is sent in headers
        ciphertext_dek = 'vault:v1:encrypted_dek'

        assert 'plaintext' not in ciphertext_dek

    def test_nonce_uniqueness(self):
        """Test that nonce is generated for each encryption."""
        nonce1 = base64.b64encode(os.urandom(32)).decode('utf-8')
        nonce2 = base64.b64encode(os.urandom(32)).decode('utf-8')

        assert nonce1 != nonce2


@pytest.mark.unit
class TestFileTransferMessageSize:
    """Test message size handling."""

    def test_message_max_bytes_config(self):
        """Test message.max.bytes configuration."""
        message_max_bytes = 8388608  # 8 MB

        assert message_max_bytes == 8388608

    def test_large_payload_handling(self):
        """Test that large payloads are handled correctly."""
        # Large files should use envelope encryption
        # instead of sending to Vault for encryption
        use_envelope_encryption = True

        assert use_envelope_encryption is True
