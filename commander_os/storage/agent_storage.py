"""
Generic Agent Storage Implementation

Provides a simplified interface for agents that don't need
custom storage logic.
"""

import uuid
from typing import Dict, Any, Optional
from pathlib import Path

from .base_storage import BaseStorage


class AgentStorage(BaseStorage):
    """
    Generic storage implementation for Commander OS agents.
    
    Provides simple key-value style storage with automatic
    table creation and basic CRUD operations.
    """
    
    def __init__(
        self,
        agent_id: str,
        data_dir: Path,
        htpc_url: Optional[str] = None,
        enable_htpc: bool = True
    ):
        super().__init__(agent_id, data_dir, htpc_url, enable_htpc)
        self._create_generic_table()
    
    def _create_generic_table(self):
        """Create a generic storage table for simple data"""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS agent_data (
                id TEXT PRIMARY KEY,
                key TEXT NOT NULL,
                value TEXT,
                data_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_agent_data_key 
                ON agent_data(key);
            
            CREATE TRIGGER IF NOT EXISTS update_agent_data_timestamp
            AFTER UPDATE ON agent_data
            BEGIN
                UPDATE agent_data SET updated_at = CURRENT_TIMESTAMP
                WHERE id = NEW.id;
            END;
        """)
        self.conn.commit()
    
    def _write_local(self, table: str, data: Dict[str, Any], operation: str):
        """Implement local write for generic storage"""
        import json
        
        if operation == "insert":
            record_id = data.get('id') or str(uuid.uuid4())
            self.conn.execute("""
                INSERT OR REPLACE INTO agent_data (id, key, value, data_type)
                VALUES (?, ?, ?, ?)
            """, (
                record_id,
                data.get('key', ''),
                json.dumps(data.get('value')),
                data.get('data_type', 'string')
            ))
        elif operation == "update":
            self.conn.execute("""
                UPDATE agent_data 
                SET value = ?, data_type = ?, updated_at = CURRENT_TIMESTAMP
                WHERE key = ?
            """, (
                json.dumps(data.get('value')),
                data.get('data_type', 'string'),
                data.get('key')
            ))
        elif operation == "delete":
            self.conn.execute(
                "DELETE FROM agent_data WHERE key = ?",
                (data.get('key'),)
            )
        
        self.conn.commit()
    
    def get(self, key: str) -> Optional[Any]:
        """Get value by key"""
        import json
        
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT value FROM agent_data WHERE key = ?",
            (key,)
        )
        row = cursor.fetchone()
        
        if row:
            return json.loads(row[0])
        return None
    
    def set(self, key: str, value: Any, data_type: str = "string") -> bool:
        """Set value by key"""
        import json
        import asyncio
        
        data = {
            'key': key,
            'value': value,
            'data_type': data_type
        }
        
        # Use event loop if available
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.write_data('agent_data', data, 'insert'))
            else:
                loop.run_until_complete(self.write_data('agent_data', data, 'insert'))
        except RuntimeError:
            # No event loop, just write locally
            self._write_local('agent_data', data, 'insert')
        
        return True
    
    def delete(self, key: str) -> bool:
        """Delete value by key"""
        import asyncio
        
        data = {'key': key}
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self.write_data('agent_data', data, 'delete'))
            else:
                loop.run_until_complete(self.write_data('agent_data', data, 'delete'))
        except RuntimeError:
            self._write_local('agent_data', data, 'delete')
        
        return True
    
    def list_all(self) -> Dict[str, Any]:
        """List all stored key-value pairs"""
        import json
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM agent_data")
        
        result = {}
        for key, value_json in cursor.fetchall():
            result[key] = json.loads(value_json)
        
        return result
