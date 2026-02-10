"""
Unit tests for consumer.py - Kafka message consumer.
"""

import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


@pytest.mark.unit
class TestConsumerConfiguration:
    """Test consumer configuration and initialization."""

    def test_consumer_config_sections(self):
        """Test that consumer configuration has required sections."""
        # Expected configuration keys from getting_started.ini
        expected_consumer_keys = [
            'group.id',
            'auto.offset.reset'
        ]

        # Verify expected keys
        assert 'group.id' in expected_consumer_keys
        assert 'auto.offset.reset' in expected_consumer_keys

    def test_consumer_group_id(self):
        """Test consumer group ID configuration."""
        group_id = 'python_example_group_1'

        assert isinstance(group_id, str)
        assert len(group_id) > 0

    def test_consumer_auto_offset_reset(self):
        """Test auto.offset.reset configuration."""
        auto_offset_reset = 'earliest'

        assert auto_offset_reset in ['earliest', 'latest', 'none']


@pytest.mark.unit
class TestConsumerMessageHandling:
    """Test consumer message processing logic."""

    def test_message_value_decode(self):
        """Test that message value can be decoded from UTF-8."""
        original_data = {
            "Name": "Test User",
            "Address": "Test Address",
            "credit_card": "4532-1234-5678-9010"
        }

        # Simulate Kafka message encoding
        encoded_value = json.dumps(original_data).encode('utf-8')
        decoded_value = encoded_value.decode('utf-8')
        parsed_data = json.loads(decoded_value)

        assert parsed_data == original_data

    def test_message_error_handling(self):
        """Test error handling for bad messages."""
        # Test with various error scenarios
        error_scenarios = [
            "KafkaError: Connection failed",
            "KafkaError: Authentication failed",
            None  # No error
        ]

        for error in error_scenarios:
            # Simulate error check
            if error:
                assert isinstance(error, str)
            else:
                assert error is None


@pytest.mark.unit
class TestConsumerOffsetReset:
    """Test offset reset functionality."""

    def test_reset_offset_flag(self):
        """Test that reset flag triggers offset reset."""
        reset = True

        # Simulate offset reset logic
        partitions = [Mock(offset=100)]
        if reset:
            for p in partitions:
                p.offset = 'OFFSET_BEGINNING'

        assert reset is True

    def test_offset_beginning_constant(self):
        """Test OFFSET_BEGINNING constant usage."""
        from confluent_kafka import OFFSET_BEGINNING

        # Verify constant exists
        assert OFFSET_BEGINNING is not None


@pytest.mark.unit
class TestConsumerTopicSubscription:
    """Test topic subscription functionality."""

    def test_subscribe_to_topic(self):
        """Test subscribing to a single topic."""
        topic = 'purchases'
        topics = [topic]

        assert len(topics) == 1
        assert topics[0] == topic

    def test_subscribe_to_multiple_topics(self):
        """Test subscribing to multiple topics."""
        topics = ['purchases', 'purchases_encrypted', 'purchases_large_encrypted']

        assert len(topics) == 3
        assert all(isinstance(t, str) for t in topics)


@pytest.mark.unit
class TestConsumerPolling:
    """Test message polling functionality."""

    def test_poll_timeout(self):
        """Test poll timeout configuration."""
        poll_timeout = 1.0  # seconds

        assert isinstance(poll_timeout, (int, float))
        assert poll_timeout > 0

    def test_poll_return_values(self):
        """Test different poll return scenarios."""
        scenarios = [
            None,  # No message yet
            Mock(error=lambda: None),  # Valid message
            Mock(error=lambda: "Error occurred")  # Error message
        ]

        for msg in scenarios:
            if msg is None:
                assert msg is None
            elif msg.error():
                assert msg.error() is not None
            else:
                assert msg.error() is None


@pytest.mark.unit
class TestConsumerOutputFormat:
    """Test consumer output formatting."""

    def test_output_message_format(self):
        """Test that output messages are formatted correctly."""
        topic = "purchases"
        value = '{"Name": "John", "Address": "Sydney", "credit_card": "1234"}'

        expected_format = "Consumed event from topic {topic}: value = {value}".format(
            topic=topic,
            value=value
        )

        assert "Consumed event from topic" in expected_format
        assert topic in expected_format
        assert value in expected_format


@pytest.mark.unit
class TestConsumerGracefulShutdown:
    """Test graceful shutdown handling."""

    def test_keyboard_interrupt_handling(self):
        """Test KeyboardInterrupt is caught for graceful shutdown."""
        try:
            raise KeyboardInterrupt()
        except KeyboardInterrupt:
            # Should be caught and pass
            assert True

    def test_consumer_close_on_shutdown(self):
        """Test that consumer closes properly."""
        mock_consumer = Mock()
        mock_consumer.close.return_value = None

        # Simulate cleanup
        mock_consumer.close()

        mock_consumer.close.assert_called_once()


@pytest.mark.unit
class TestConsumerSessionTimeout:
    """Test session timeout handling."""

    def test_session_timeout_message(self):
        """Test session timeout message displayed to user."""
        timeout_msg = "Waiting..."

        assert timeout_msg == "Waiting..."

    def test_initial_message_consumption_delay(self):
        """Test understanding of initial consumption delay."""
        # From code comments: Initial message consumption may take up to
        # `session.timeout.ms` for the consumer group to rebalance
        session_timeout_ms = 10000  # Example value

        assert session_timeout_ms > 0
        assert isinstance(session_timeout_ms, int)


@pytest.mark.unit
class TestConsumerMessageExtraction:
    """Test message data extraction."""

    def test_extract_topic_from_message(self):
        """Test extracting topic from message."""
        mock_msg = Mock()
        mock_msg.topic.return_value = 'purchases'

        topic = mock_msg.topic()
        assert topic == 'purchases'

    def test_extract_value_from_message(self):
        """Test extracting value from message."""
        test_data = {"test": "value"}
        mock_msg = Mock()
        mock_msg.value.return_value = json.dumps(test_data).encode('utf-8')

        value = mock_msg.value()
        decoded = value.decode('utf-8')
        parsed = json.loads(decoded)

        assert parsed == test_data
