"""
Base Storage Class for Commander OS Agents

Provides core storage functionality with:
- Local SQLite cache (WAL mode)
- Dual-write strategy (local + HTPC)
- Network-wide data visibility
- Resilient error handling
"""

import sqlite3
import asyncio
import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

try:
    import httpx
except ImportError:
    httpx = None


logger = logging.getLogger(__name__)


class BaseStorage:
    """
    Base storage class for Commander OS agents.
    
    Implements local-first architecture with dual-write strategy for
    network-wide visibility. Uses SQLite with WAL mode for local cache
    and HTTP API for HTPC synchronization.
    """
    
    def __init__(
        self,
        agent_id: str,
        data_dir: Path,
        htpc_url: Optional[str] = None,
        enable_htpc: bool = True
    ):
        """
        Initialize base storage.
        
        Args:
            agent_id: Unique identifier for the agent
            data_dir: Directory for local database storage
            htpc_url: URL of the HTPC relay service
            enable_htpc: Whether to enable HTPC synchronization
        """
        self.agent_id = agent_id
        self.data_dir = Path(data_dir)
        self.db_path = self.data_dir / f"{agent_id}.db"
        self.htpc_url = htpc_url
        self.enable_htpc = enable_htpc and htpc_url is not None
        
        self.conn: Optional[sqlite3.Connection] = None
        self.http_client: Optional[Any] = None
        
        # Sync queue tracking
        self.sync_queue_table = "sync_queue"
        
        self._initialize()
    
    def _initialize(self):
        """Initialize storage system"""
        # Create data directory if needed
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize SQLite connection
        self._init_sqlite()
        
        # Initialize HTTP client for HTPC if enabled
        if self.enable_htpc:
            self._init_http_client()
        
        # Create base tables
        self._create_base_tables()
        
        logger.info(f"Storage initialized for agent {self.agent_id}")
    
    def _init_sqlite(self):
        """Initialize SQLite connection with WAL mode"""
        self.conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=30.0
        )
        
        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
        self.conn.execute("PRAGMA temp_store=MEMORY")
        
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys=ON")
        
        logger.info(f"SQLite initialized at {self.db_path}")
    
    def _init_http_client(self):
        """Initialize HTTP client for HTPC communication"""
        if httpx is None:
            logger.warning("httpx not installed, HTPC sync disabled")
            self.enable_htpc = False
            return
        
        self.http_client = httpx.AsyncClient(
            timeout=httpx.Timeout(5.0, connect=2.0),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )
        logger.info(f"HTTP client initialized for HTPC at {self.htpc_url}")
    
    def _create_base_tables(self):
        """Create base tables needed for all agents"""
        self.conn.executescript(f"""
            CREATE TABLE IF NOT EXISTS {self.sync_queue_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                operation TEXT NOT NULL,
                data TEXT NOT NULL,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retry_count INTEGER DEFAULT 0
            );
            
            CREATE INDEX IF NOT EXISTS idx_sync_queue_queued_at 
                ON {self.sync_queue_table}(queued_at);
            
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            );
        """)
        self.conn.commit()
        logger.info("Base tables created")
    
    async def write_data(
        self,
        table: str,
        data: Dict[str, Any],
        operation: str = "insert"
    ) -> bool:
        """
        Dual-write data to local cache and HTPC.
        
        Args:
            table: Target table name
            data: Data to write
            operation: Operation type (insert, update, delete)
            
        Returns:
            True if write succeeded (at least locally)
        """
        try:
            # 1. Write to local cache first (fast, reliable)
            self._write_local(table, data, operation)
            
            # 2. Write to HTPC (network visibility)
            if self.enable_htpc:
                await self._write_htpc(table, data, operation)
            
            return True
            
        except Exception as e:
            logger.error(f"Write failed for table {table}: {e}")
            return False
    
    def _write_local(self, table: str, data: Dict[str, Any], operation: str):
        """Write data to local SQLite database"""
        # Subclasses implement specific SQL logic
        # This method should be overridden
        raise NotImplementedError("Subclasses must implement _write_local")
    
    async def _write_htpc(
        self,
        table: str,
        data: Dict[str, Any],
        operation: str
    ):
        """
        Write data to HTPC via HTTP API.
        
        On failure, queues data for later synchronization.
        """
        if not self.enable_htpc or self.http_client is None:
            return
        
        try:
            endpoint = f"{self.htpc_url}/relay/immediate"
            payload = {
                "agent_id": self.agent_id,
                "table": table,
                "operation": operation,
                "data": data,
                "timestamp": time.time()
            }
            
            response = await asyncio.wait_for(
                self.http_client.post(endpoint, json=payload),
                timeout=2.0
            )
            response.raise_for_status()
            
            logger.debug(f"HTPC write succeeded for {table}")
            
        except asyncio.TimeoutError:
            logger.warning(f"HTPC write timeout for {table}, queueing")
            self._queue_for_sync(table, data, operation)
            
        except Exception as e:
            logger.warning(f"HTPC write failed for {table}: {e}, queueing")
            self._queue_for_sync(table, data, operation)
    
    def _queue_for_sync(self, table: str, data: Dict[str, Any], operation: str):
        """Queue data for later HTPC synchronization"""
        try:
            self.conn.execute(
                f"""INSERT INTO {self.sync_queue_table} 
                    (table_name, operation, data) 
                    VALUES (?, ?, ?)""",
                (table, operation, json.dumps(data))
            )
            self.conn.commit()
            logger.debug(f"Queued {operation} for {table}")
        except Exception as e:
            logger.error(f"Failed to queue for sync: {e}")
    
    async def batch_write(self, records: List[Dict[str, Any]]) -> int:
        """
        Write multiple records efficiently.
        
        Args:
            records: List of records, each with 'table', 'data', 'operation'
            
        Returns:
            Number of records successfully written locally
        """
        success_count = 0
        
        # Write all to local first
        for record in records:
            try:
                self._write_local(
                    record['table'],
                    record['data'],
                    record.get('operation', 'insert')
                )
                success_count += 1
            except Exception as e:
                logger.error(f"Batch local write failed: {e}")
        
        # Send batch to HTPC
        if self.enable_htpc and success_count > 0:
            await self._batch_write_htpc(records)
        
        return success_count
    
    async def _batch_write_htpc(self, records: List[Dict[str, Any]]):
        """Send batch of records to HTPC"""
        if not self.enable_htpc or self.http_client is None:
            return
        
        try:
            endpoint = f"{self.htpc_url}/relay/batch"
            payload = {
                "agent_id": self.agent_id,
                "records": records,
                "timestamp": time.time()
            }
            
            response = await asyncio.wait_for(
                self.http_client.post(endpoint, json=payload),
                timeout=5.0
            )
            response.raise_for_status()
            
            logger.info(f"Batch write succeeded for {len(records)} records")
            
        except Exception as e:
            logger.warning(f"Batch HTPC write failed: {e}, queueing individually")
            for record in records:
                self._queue_for_sync(
                    record['table'],
                    record['data'],
                    record.get('operation', 'insert')
                )
    
    def query_local(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> List[Tuple]:
        """
        Query data from local cache.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of result tuples
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute(query, params or ())
            return cursor.fetchall()
        except Exception as e:
            logger.error(f"Local query failed: {e}")
            return []
    
    async def query_network(
        self,
        query: str,
        params: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Query data from HTPC (network-wide view).
        
        Args:
            query: Query description or SQL
            params: Query parameters
            
        Returns:
            List of result dictionaries
        """
        if not self.enable_htpc or self.http_client is None:
            logger.warning("HTPC not available, using local cache")
            return []
        
        try:
            endpoint = f"{self.htpc_url}/relay/query"
            payload = {
                "agent_id": self.agent_id,
                "query": query,
                "params": params or {}
            }
            
            response = await asyncio.wait_for(
                self.http_client.post(endpoint, json=payload),
                timeout=5.0
            )
            response.raise_for_status()
            
            return response.json().get('results', [])
            
        except Exception as e:
            logger.error(f"Network query failed: {e}")
            return []
    
    async def process_sync_queue(self, batch_size: int = 100) -> int:
        """
        Process queued sync operations.
        
        Args:
            batch_size: Maximum number of records to process
            
        Returns:
            Number of records successfully synced
        """
        if not self.enable_htpc:
            return 0
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT id, table_name, operation, data 
            FROM {self.sync_queue_table}
            WHERE retry_count < 5
            ORDER BY queued_at ASC
            LIMIT ?
        """, (batch_size,))
        
        records = cursor.fetchall()
        if not records:
            return 0
        
        success_count = 0
        
        for record_id, table, operation, data_json in records:
            try:
                data = json.loads(data_json)
                await self._write_htpc(table, data, operation)
                
                # Remove from queue on success
                self.conn.execute(
                    f"DELETE FROM {self.sync_queue_table} WHERE id = ?",
                    (record_id,)
                )
                self.conn.commit()
                success_count += 1
                
            except Exception as e:
                logger.error(f"Sync queue processing failed for record {record_id}: {e}")
                # Increment retry count
                self.conn.execute(
                    f"""UPDATE {self.sync_queue_table} 
                        SET retry_count = retry_count + 1 
                        WHERE id = ?""",
                    (record_id,)
                )
                self.conn.commit()
        
        logger.info(f"Processed {success_count}/{len(records)} queued records")
        return success_count
    
    def get_sync_queue_size(self) -> int:
        """Get number of records waiting for sync"""
        cursor = self.conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {self.sync_queue_table}")
        return cursor.fetchone()[0]
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check storage health.
        
        Returns:
            Health status dictionary
        """
        health = {
            "agent_id": self.agent_id,
            "local_db": False,
            "htpc_enabled": self.enable_htpc,
            "sync_queue_size": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Check local database
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1")
            health["local_db"] = True
        except Exception as e:
            logger.error(f"Local DB health check failed: {e}")
        
        # Check sync queue
        try:
            health["sync_queue_size"] = self.get_sync_queue_size()
        except Exception as e:
            logger.error(f"Sync queue check failed: {e}")
        
        return health
    
    async def close(self):
        """Close storage connections"""
        if self.conn:
            self.conn.close()
            logger.info("Local database connection closed")
        
        if self.http_client:
            await self.http_client.aclose()
            logger.info("HTTP client closed")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        if self.conn:
            self.conn.close()
