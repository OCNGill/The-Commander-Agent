"""
The-Commander: Relay Client
Utility for sending messages to the central Relay Server.

Version: 1.2.0 (FastAPI/HTTP-based)
"""

import logging
import httpx
from typing import Optional, Any, Dict

from commander_os.core.protocol import MessageEnvelope

logger = logging.getLogger(__name__)

class RelayClient:
    """
    Client for interacting with the cluster's Relay Server.
    """
    
    def __init__(self, relay_url: str = "http://10.0.0.42:8001"):
        self.relay_url = relay_url.rstrip('/')
        self._client = httpx.Client(timeout=10.0)
        
        logger.info(f"RelayClient initialized for {self.relay_url}")

    def send_message(self, envelope: MessageEnvelope) -> bool:
        """
        Send a protocol envelope to the relay.
        """
        endpoint = f"{self.relay_url}/relay/message"
        
        try:
            logger.debug(f"Sending {envelope.msg_type} to relay...")
            response = self._client.post(endpoint, json=envelope.dict())
            
            if response.status_code == 200:
                logger.debug(f"Message {envelope.id} successfully relayed")
                return True
            else:
                logger.error(f"Relay rejected message {envelope.id}: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to relay at {self.relay_url}: {e}")
            return False

    def check_health(self) -> bool:
        """Check if the relay is reachable."""
        try:
            response = self._client.get(f"{self.relay_url}/health")
            return response.status_code == 200
        except Exception:
            return False

    def close(self):
        """Close the underlying HTTP client."""
        self._client.close()
