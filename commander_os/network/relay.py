"""
The-Commander: Relay Server
Central message hub for the cluster.

Handles:
- Receiving MessageEnvelopes from agents/commander
- Persisting all traffic to MessageStore (HTPC local)
- Routing messages to recipients

Version: 1.2.1 (Config Integrated)
"""

import logging
import os
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
import uvicorn

from commander_os.core.protocol import MessageEnvelope, CommanderProtocol
from commander_os.core.memory import MessageStore
from commander_os.core.config_manager import ConfigManager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="The Commander: Relay Server")

# Initialize Config & Store
# In production, this would be on HTPC
config = ConfigManager()
config.load_relay_config()

# The database should be on the ZFS mountpoint on HTPC
# For now, we utilize the current directory or a configured path
db_url = os.getenv("COMMANDER_DB_URL", "sqlite:///commander_memory.db")
store = MessageStore(db_url)

@app.get("/health")
async def health():
    return {"status": "ok", "service": "relay"}

@app.post("/relay/message")
async def receive_message(envelope: MessageEnvelope, background_tasks: BackgroundTasks):
    """
    Standard endpoint for all cluster traffic.
    """
    logger.info(f"Received {envelope.msg_type} from {envelope.sender_id} -> {envelope.recipient_id}")
    
    # 1. Validate Envelope
    if not CommanderProtocol.validate_envelope(envelope):
        logger.error(f"Invalid envelope received: {envelope.id}")
        raise HTTPException(status_code=400, detail="Invalid protocol envelope")

    # 2. Persist to Message Store
    background_tasks.add_task(persist_envelope, envelope)
    
    # 3. TODO: Routing Logic 
    # forward_to_recipient(envelope)
    
    return {"status": "received", "id": envelope.id}

def persist_envelope(envelope: MessageEnvelope):
    """Worker task to write envelope to SQL."""
    try:
        # Determine role from metadata or task reference
        role = envelope.metadata.get("role", "unknown")
        
        store.log_message(
            task_id=envelope.task_id or "system",
            sender=envelope.sender_id,
            recipient=envelope.recipient_id,
            role=role,
            content=str(envelope.payload),
            metadata=envelope.metadata
        )
        logger.debug(f"Persisted message {envelope.id}")
    except Exception as e:
        logger.error(f"Failed to persist message {envelope.id}: {e}")

def start_relay():
    """Start the relay server using values from config."""
    relay_cfg = config.relay
    host = relay_cfg.host if relay_cfg else "0.0.0.0"
    port = relay_cfg.port if relay_cfg else 8001
    
    logger.info(f"Starting Relay on {host}:{port}...")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_relay()
