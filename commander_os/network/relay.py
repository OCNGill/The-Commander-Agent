"""
The-Commander: Relay Server
Central message hub for the cluster.

Handles:
- Receiving MessageEnvelopes from agents/commander
- Persisting all traffic to MessageStore (HTPC local)
- Routing messages to recipients
- Agent storage synchronization (immediate, batch, query)

Version: 1.2.2 (Storage Endpoints Added)
"""

import logging
import os
import sqlite3
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
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

# Storage sync directory (where agent databases are stored on HTPC)
storage_dir = Path(os.getenv("COMMANDER_STORAGE_DIR", "./data/agent_storage"))
storage_dir.mkdir(parents=True, exist_ok=True)

# Pydantic models for storage endpoints
class ImmediateWriteRequest(BaseModel):
    agent_id: str
    table: str
    operation: str
    data: Dict[str, Any]
    timestamp: float

class BatchWriteRequest(BaseModel):
    agent_id: str
    records: List[Dict[str, Any]]
    timestamp: float

class QueryRequest(BaseModel):
    agent_id: str
    query: str
    params: Optional[Dict[str, Any]] = None

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

# ============================================================
# STORAGE SYNCHRONIZATION ENDPOINTS
# ============================================================

def get_agent_db_connection(agent_id: str) -> sqlite3.Connection:
    """Get or create SQLite connection for an agent's database"""
    db_path = storage_dir / f"{agent_id}.db"
    conn = sqlite3.connect(db_path, check_same_thread=False)
    
    # Enable WAL mode
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    
    return conn

@app.post("/relay/immediate")
async def immediate_write(request: ImmediateWriteRequest, background_tasks: BackgroundTasks):
    """
    Immediate write endpoint for dual-write strategy.
    Writes single record to HTPC for network-wide visibility.
    """
    logger.info(f"Immediate write: {request.agent_id} -> {request.table}")
    
    try:
        # Process write in background to avoid blocking
        background_tasks.add_task(
            _process_immediate_write,
            request.agent_id,
            request.table,
            request.operation,
            request.data
        )
        
        return {"status": "accepted", "agent_id": request.agent_id}
        
    except Exception as e:
        logger.error(f"Immediate write failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _process_immediate_write(agent_id: str, table: str, operation: str, data: Dict[str, Any]):
    """Background task to process immediate write"""
    try:
        conn = get_agent_db_connection(agent_id)
        
        # Create table if it doesn't exist (generic structure)
        _ensure_table_exists(conn, table)
        
        # Execute write operation
        if operation == "insert":
            _insert_record(conn, table, data)
        elif operation == "update":
            _update_record(conn, table, data)
        elif operation == "delete":
            _delete_record(conn, table, data)
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Processed immediate write for {agent_id}.{table}")
        
    except Exception as e:
        logger.error(f"Failed to process immediate write: {e}")

@app.post("/relay/batch")
async def batch_write(request: BatchWriteRequest, background_tasks: BackgroundTasks):
    """
    Batch write endpoint for efficient bulk operations.
    Writes multiple records to HTPC.
    """
    logger.info(f"Batch write: {request.agent_id} -> {len(request.records)} records")
    
    try:
        background_tasks.add_task(
            _process_batch_write,
            request.agent_id,
            request.records
        )
        
        return {"status": "accepted", "agent_id": request.agent_id, "count": len(request.records)}
        
    except Exception as e:
        logger.error(f"Batch write failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _process_batch_write(agent_id: str, records: List[Dict[str, Any]]):
    """Background task to process batch write"""
    try:
        conn = get_agent_db_connection(agent_id)
        
        for record in records:
            table = record.get('table')
            operation = record.get('operation', 'insert')
            data = record.get('data', {})
            
            _ensure_table_exists(conn, table)
            
            if operation == "insert":
                _insert_record(conn, table, data)
            elif operation == "update":
                _update_record(conn, table, data)
            elif operation == "delete":
                _delete_record(conn, table, data)
        
        conn.commit()
        conn.close()
        
        logger.info(f"Processed batch write for {agent_id}: {len(records)} records")
        
    except Exception as e:
        logger.error(f"Failed to process batch write: {e}")

@app.post("/relay/query")
async def query_data(request: QueryRequest):
    """
    Query endpoint for network-wide data access.
    Allows agents to query other agents' data from HTPC.
    """
    logger.info(f"Query: {request.agent_id}")
    
    try:
        conn = get_agent_db_connection(request.agent_id)
        cursor = conn.cursor()
        
        # Execute query (basic support - could be enhanced)
        # For now, we support direct SQL queries
        cursor.execute(request.query)
        rows = cursor.fetchall()
        
        # Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Convert to list of dicts
        results = []
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        conn.close()
        
        return {"status": "success", "results": results}
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# STORAGE HELPER FUNCTIONS
# ============================================================

def _ensure_table_exists(conn: sqlite3.Connection, table: str):
    """Create table if it doesn't exist (generic structure)"""
    try:
        # Check if table exists
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (table,)
        )
        
        if cursor.fetchone() is None:
            # Create generic table structure
            cursor.execute(f"""
                CREATE TABLE {table} (
                    id TEXT PRIMARY KEY,
                    data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            logger.info(f"Created table {table}")
            
    except Exception as e:
        logger.error(f"Failed to ensure table exists: {e}")

def _insert_record(conn: sqlite3.Connection, table: str, data: Dict[str, Any]):
    """Insert record into table"""
    # Store entire data object as JSON in generic table
    record_id = data.get('id', str(data))
    cursor = conn.cursor()
    cursor.execute(
        f"INSERT OR REPLACE INTO {table} (id, data) VALUES (?, ?)",
        (record_id, json.dumps(data))
    )

def _update_record(conn: sqlite3.Connection, table: str, data: Dict[str, Any]):
    """Update record in table"""
    record_id = data.get('id')
    if not record_id:
        raise ValueError("Update requires 'id' field")
    
    cursor = conn.cursor()
    cursor.execute(
        f"UPDATE {table} SET data=?, updated_at=CURRENT_TIMESTAMP WHERE id=?",
        (json.dumps(data), record_id)
    )

def _delete_record(conn: sqlite3.Connection, table: str, data: Dict[str, Any]):
    """Delete record from table"""
    record_id = data.get('id')
    if not record_id:
        raise ValueError("Delete requires 'id' field")
    
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id=?", (record_id,))

def start_relay():
    """Start the relay server using values from config."""
    relay_cfg = config.relay
    host = relay_cfg.host if relay_cfg else "0.0.0.0"
    port = relay_cfg.port if relay_cfg else 8001
    
    logger.info(f"Starting Relay on {host}:{port}...")
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    start_relay()
