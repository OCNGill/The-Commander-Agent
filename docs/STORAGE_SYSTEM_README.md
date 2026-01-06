# Commander OS Storage System

**Version:** 1.0.0  
**Status:** ✅ Implemented  
**Last Updated:** January 6, 2026

## Overview

The Commander OS Storage System provides a robust, local-first storage architecture with network-wide visibility for agents. It implements a dual-write strategy that ensures data is both fast (local NVMe) and accessible cluster-wide (HTPC central repository).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Commander OS Cluster                      │
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │   Node 1     │      │   Node 2     │      │   Node 3  │ │
│  │              │      │              │      │           │ │
│  │ ┌──────────┐ │      │ ┌──────────┐ │      │ ┌───────┐│ │
│  │ │Agent A   │ │      │ │Agent B   │ │      │ │Agent C││ │
│  │ │Local DB  │ │      │ │Local DB  │ │      │ │Local  ││ │
│  │ │(SQLite)  │ │      │ │(SQLite)  │ │      │ │DB     ││ │
│  │ └────┬─────┘ │      │ └────┬─────┘ │      │ └───┬───┘│ │
│  └──────┼───────┘      └──────┼───────┘      └─────┼────┘ │
│         │                     │                     │      │
│         │  Dual-Write (HTTP)  │                     │      │
│         └─────────────────────┼─────────────────────┘      │
│                               │                            │
│                    ┌──────────▼──────────┐                 │
│                    │   HTPC Relay        │                 │
│                    │   Storage Endpoints │                 │
│                    │   /relay/immediate  │                 │
│                    │   /relay/batch      │                 │
│                    │   /relay/query      │                 │
│                    └──────────┬──────────┘                 │
│                               │                            │
│                    ┌──────────▼──────────┐                 │
│                    │ Central Storage     │                 │
│                    │ (SQLite on ZFS)     │                 │
│                    │ Network-wide Access │                 │
│                    └─────────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

## Key Features

### ✅ Local-First Performance
- **SQLite with WAL mode** for sub-millisecond local operations
- **NVMe storage** for maximum speed
- **No network dependency** for local reads/writes

### ✅ Network-Wide Visibility
- **Dual-write strategy** writes to both local and HTPC simultaneously
- **Real-time sync** ensures immediate cluster-wide data access
- **Query endpoints** allow agents to query other agents' data

### ✅ Resilient Architecture
- **Sync queue** handles HTPC downtime gracefully
- **Automatic retry** for failed synchronizations
- **Health monitoring** tracks storage system status

### ✅ Agent-Optimized
- **Base classes** for easy agent integration
- **Schema migration** support
- **Indexed queries** for performance

## Components

### 1. BaseStorage
**Location:** `commander_os/storage/base_storage.py`

Core storage functionality:
- SQLite initialization with WAL mode
- Dual-write implementation
- Sync queue management
- Health monitoring

### 2. AgentStorage
**Location:** `commander_os/storage/agent_storage.py`

Generic key-value storage for simple agents:
- Simple get/set/delete operations
- Automatic JSON serialization
- Built on BaseStorage

### 3. RecruiterAgentStorage
**Location:** `commander_os/agents/recruiter/storage.py`

Specialized storage for Recruiter Agent:
- Candidate management
- Interview tracking
- Job requisitions
- Skills-based search

### 4. HTPC Relay Endpoints
**Location:** `commander_os/network/relay.py`

HTTP endpoints for storage sync:
- `/relay/immediate` - Real-time single writes
- `/relay/batch` - Bulk operations
- `/relay/query` - Network-wide queries

## Quick Start

### For Agent Developers

```python
from pathlib import Path
from commander_os.storage.agent_storage import AgentStorage

# Initialize storage
storage = AgentStorage(
    agent_id="my-agent",
    data_dir=Path("./data/agents/my-agent"),
    htpc_url="http://10.0.0.42:8001",
    enable_htpc=True
)

# Store data
storage.set('config', {'setting': 'value'})

# Retrieve data
config = storage.get('config')

# Cleanup
await storage.close()
```

### For Custom Storage Schemas

See [`Commander_OS_agent_storage_info.md`](./Commander_OS_agent_storage_info.md) for a comprehensive guide on designing custom storage for your agent.

## Configuration

### Storage Configuration
**File:** `config/storage_config.yaml`

```yaml
agent_storage:
  local_data_dir: "./data/agents"
  htpc_url: "http://10.0.0.42:8001"
  enable_htpc: true
  sync_interval: 60
  sync_batch_size: 100
  max_retry_count: 5
```

### Relay Configuration
**File:** `config/relay.yaml`

```yaml
relay:
  host: 10.0.0.42
  port: 8001
  agent_storage_dir: /gillsystems_zfs_pool/AI_storage/agent_storage
  enable_storage_sync: true
```

## Usage Examples

### Example 1: Basic Storage Operations

```python
import asyncio
from pathlib import Path
from commander_os.storage.agent_storage import AgentStorage

async def main():
    storage = AgentStorage(
        agent_id="example-agent",
        data_dir=Path("./data/agents/example"),
        enable_htpc=False  # Local only for testing
    )
    
    # Store data
    storage.set('user_preferences', {
        'theme': 'dark',
        'notifications': True
    })
    
    # Retrieve data
    prefs = storage.get('user_preferences')
    print(f"Theme: {prefs['theme']}")
    
    # List all data
    all_data = storage.list_all()
    print(f"Stored keys: {list(all_data.keys())}")
    
    # Cleanup
    await storage.close()

asyncio.run(main())
```

### Example 2: Recruiter Agent Integration

See [`commander_os/agents/recruiter/storage_example.py`](../commander_os/agents/recruiter/storage_example.py) for a complete working example with:
- Candidate management
- Interview scheduling
- Job requisitions
- Skills-based search
- Agent interactions

## Testing

Run the storage tests:

```bash
pytest tests/test_storage.py -v
```

Test coverage includes:
- BaseStorage functionality
- AgentStorage operations
- RecruiterAgentStorage queries
- HTPC integration (mocked)
- Sync queue processing
- Health monitoring

## Performance Considerations

### Local Operations
- **Read latency:** < 1ms (SQLite + WAL mode)
- **Write latency:** < 10ms (local only)
- **Throughput:** 1000+ ops/sec

### Network Operations
- **Dual-write latency:** < 200ms (local + HTPC)
- **Batch operations:** Optimized for bulk writes
- **Query latency:** < 100ms (HTPC query)

### Optimization Tips

1. **Use indexes** for frequently queried columns
2. **Batch writes** when possible for efficiency
3. **Query locally** for speed, network for completeness
4. **Monitor sync queue** to prevent backlog

## Monitoring

### Health Check

```python
health = storage.health_check()
print(health)
# Output:
# {
#   'agent_id': 'my-agent',
#   'local_db': True,
#   'htpc_enabled': True,
#   'sync_queue_size': 0,
#   'timestamp': '2026-01-06T12:00:00'
# }
```

### Sync Queue Management

```python
# Check queue size
queue_size = storage.get_sync_queue_size()
print(f"Pending syncs: {queue_size}")

# Process queue
synced = await storage.process_sync_queue(batch_size=100)
print(f"Synced {synced} records")
```

## Troubleshooting

### Issue: High Sync Queue Size
**Cause:** HTPC is unavailable or slow  
**Solution:** 
```python
# Process queue manually
await storage.process_sync_queue(batch_size=1000)

# Or check HTPC connectivity
health = storage.health_check()
if health['sync_queue_size'] > 100:
    print("Warning: Large sync queue detected")
```

### Issue: Slow Queries
**Cause:** Missing indexes  
**Solution:** Add indexes to your schema
```sql
CREATE INDEX idx_column_name ON table_name(column_name);
```

### Issue: Database Locked
**Cause:** WAL mode not enabled  
**Solution:** Verify WAL mode
```python
cursor = storage.conn.cursor()
cursor.execute("PRAGMA journal_mode")
result = cursor.fetchone()
assert result[0] == 'wal'
```

## Migration Guide

### From No Storage to Storage

1. **Create storage instance** in your agent
2. **Define schema** (see guide)
3. **Implement operations** (add, update, query)
4. **Test locally** (disable HTPC initially)
5. **Enable HTPC** sync

### Schema Versioning

Use the `schema_version` table:

```python
def migrate_to_v2(conn):
    """Migrate schema to version 2"""
    conn.executescript("""
        ALTER TABLE candidates ADD COLUMN linkedin_url TEXT;
        INSERT INTO schema_version (version, description) 
        VALUES (2, 'Added LinkedIn URL field');
    """)
    conn.commit()
```

## Future Enhancements

- [ ] **Replication** - Multi-HTPC setup for redundancy
- [ ] **Encryption** - At-rest and in-transit encryption
- [ ] **Compression** - Reduce storage footprint
- [ ] **Analytics** - Built-in query analytics
- [ ] **Backup/Restore** - Automated backup system

## Resources

- **Developer Guide:** [`Commander_OS_agent_storage_info.md`](./Commander_OS_agent_storage_info.md)
- **Architecture Doc:** [`STORAGE_ARCHITECTURE.md`](./STORAGE_ARCHITECTURE.md)
- **Example Code:** [`storage_example.py`](../commander_os/agents/recruiter/storage_example.py)
- **Test Suite:** [`tests/test_storage.py`](../tests/test_storage.py)

## Support

For questions or issues:
1. Check the [troubleshooting section](#troubleshooting)
2. Review the [developer guide](./Commander_OS_agent_storage_info.md)
3. Open an issue on GitHub

---

**Built with ❤️ for Commander OS**  
*Local-first, network-wide, always reliable.*
