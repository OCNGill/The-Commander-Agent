"""
Test Suite: Relay Server
Tests for commander_os.network.relay

Run with: pytest tests/network/test_relay.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch

from commander_os.network.relay import app
from commander_os.core.protocol import CommanderProtocol, MessageEnvelope, MessageType

client = TestClient(app)

class TestRelay:
    """Tests for the Relay Server."""

    def test_health_check(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_receive_message_success(self):
        """Test sending a valid MessageEnvelope to the relay."""
        # Create a valid message
        envelope = CommanderProtocol.create_command(
            sender_id="commander",
            recipient_id="agent-1",
            command="test",
            task_id="task-123"
        )
        
        # We mock persist_envelope to avoid SQL issues in simple unit test
        with patch('commander_os.network.relay.persist_envelope') as mock_persist:
            response = client.post("/relay/message", json=envelope.dict())
            
            assert response.status_code == 200
            assert response.json()["status"] == "received"
            assert response.json()["id"] == envelope.id
            
            # Since it's a background task, we might need a small wait or just verify it was added
            # In TestClient, background tasks run synchronously by default unless configured otherwise
            mock_persist.assert_called_once()

    def test_receive_invalid_protocol(self):
        """Test that invalid envelopes are rejected."""
        # Missing sender_id
        bad_msg = {
            "msg_type": "command",
            "recipient_id": "agent-1",
            "payload": {}
        }
        
        # This will fail Pydantic validation first
        response = client.post("/relay/message", json=bad_msg)
        assert response.status_code == 422 # Unprocessable Entity (Pydantic)

    def test_persistence_logic(self):
        """Test that the persistence background task calls MessageStore."""
        envelope = CommanderProtocol.create_command(
            sender_id="commander",
            recipient_id="agent-1",
            command="test",
            task_id="task-123"
        )
        
        with patch('commander_os.network.relay.store') as mock_store:
            from commander_os.network.relay import persist_envelope
            persist_envelope(envelope)
            
            mock_store.log_message.assert_called_once()
            args, kwargs = mock_store.log_message.call_args
            assert kwargs["task_id"] == "task-123"
            assert kwargs["sender"] == "commander"
            assert kwargs["recipient"] == "agent-1"
