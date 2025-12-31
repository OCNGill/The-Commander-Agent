"""
Test Suite: Network Layer
Tests for Relay and RelayClient

Run with: pytest tests/network/test_network.py -v
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import httpx

from commander_os.network.relay import app
from commander_os.network.relay_client import RelayClient
from commander_os.core.protocol import CommanderProtocol, MessageEnvelope, MessageType

# Test Relay directly using TestClient
relay_test_client = TestClient(app)

class TestNetworkStack:
    """Integrated tests for Relay + Client."""

    def test_relay_health(self):
        response = relay_test_client.get("/health")
        assert response.status_code == 200

    @patch('httpx.Client.post')
    def test_client_send_success(self, mock_post):
        """Test RelayClient sending to a mocked Relay endpoint."""
        relay_url = "http://10.0.0.42:8001"
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"status": "received"})
        
        client = RelayClient(relay_url)
        envelope = CommanderProtocol.create_command("commander", "agent-1", "test")
        
        success = client.send_message(envelope)
        assert success is True
        mock_post.assert_called_once()

    @patch('httpx.Client.post')
    def test_client_relay_failure(self, mock_post):
        """Test RelayClient handling relay errors."""
        relay_url = "http://10.0.0.42:8001"
        mock_post.return_value = MagicMock(status_code=500, text="Internal Server Error")
        
        client = RelayClient(relay_url)
        envelope = CommanderProtocol.create_command("commander", "agent-1", "test")
        
        success = client.send_message(envelope)
        assert success is False

    @patch('httpx.Client.get')
    def test_client_health_check(self, mock_get):
        relay_url = "http://10.0.0.42:8001"
        mock_get.return_value = MagicMock(status_code=200, json=lambda: {"status": "ok"})
        
        client = RelayClient(relay_url)
        assert client.check_health() is True
