# Commander OS Agent Storage Guide

**Version:** 1.0.0  
**Last Updated:** January 6, 2026  
**Purpose:** Guide for designing and implementing storage for Commander OS agents

---

## Overview

This guide provides a practical framework for designing storage systems for Commander OS agents. It's based on the architecture developed for the Gillsystems-Recruiter-Agent and applies to all agents operating within the Commander OS ecosystem.

---

## Core Storage Principles

### 1. **Local-First Architecture**
- **Primary Storage:** Local NVMe SQLite database (WAL mode)
- **Why:** Agents need fast, reliable local access to their data
- **Benefit:** Sub-millisecond read/write operations, no network dependency for local operations

### 2. **Network-Wide Visibility**
- **Secondary Storage:** HTPC central repository via HTTP API
- **Why:** Enable cluster-wide data access and agent collaboration
- **Benefit:** Any node can query any agent's data in real-time

### 3. **Dual-Write Strategy**
- **Approach:** Write to both local cache AND HTPC simultaneously
- **Why:** Immediate network visibility without waiting for async sync
- **Benefit:** Real-time data consistency across the cluster

---

## Storage Design Schema

When designing storage for your agent, answer these questions:

### 1. **What Data Does Your Agent Store?**

Identify the types of data your agent will manage:

- **Transactional Data:** Events, actions, decisions
- **State Data:** Current status, configuration, preferences
- **Historical Data:** Logs, audit trails, metrics
- **Corpus Data:** Knowledge base, learned patterns, insights
- **Relational Data:** Connections to other agents, tasks, or entities

**Example (Recruiter Agent):**
```yaml
Data Types:
  - Candidate profiles (name, skills, experience)
  - Interview records (date, notes, outcome)
  - Job requisitions (title, requirements, status)
  - Agent interactions (which agents were consulted)
  - Search history (queries, results, effectiveness)
```

### 2. **What Are Your Agent's Read/Write Patterns?**

Define how your agent interacts with data:

- **Read Frequency:** High/Medium/Low
- **Write Frequency:** High/Medium/Low
- **Query Complexity:** Simple lookups vs complex joins
- **Data Volume:** Small (KB), Medium (MB), Large (GB+)
- **Retention Period:** Hours, days, months, permanent

**Example (Recruiter Agent):**
```yaml
Access Patterns:
  Candidate Profiles:
    - Read: High (every search query)
    - Write: Medium (new candidates added regularly)
    - Query: Complex (skill matching, experience filtering)
    - Volume: Medium (100s of KB per profile)
    - Retention: Permanent
  
  Interview Records:
    - Read: Medium (review before decisions)
    - Write: Low (after each interview)
    - Query: Simple (by candidate, by date)
    - Volume: Small (few KB per record)
    - Retention: Permanent (audit trail)
```

### 3. **What Data Needs Network Visibility?**

Determine which data other agents or nodes need to access:

- **Always Visible:** Critical data needed by other agents
- **On-Demand Visible:** Data shared when requested
- **Private:** Local-only data, never shared

**Example (Recruiter Agent):**
```yaml
Visibility Levels:
  Always Visible:
    - Active job requisitions (other agents may recommend candidates)
    - Candidate status updates (for coordination)
  
  On-Demand Visible:
    - Full candidate profiles (when another agent needs details)
    - Interview schedules (when coordination is needed)
  
  Private:
    - Internal scoring algorithms
    - Draft notes and incomplete assessments
```

### 4. **What Are Your Performance Requirements?**

Define your agent's performance needs:

- **Response Time:** How fast must reads complete?
- **Throughput:** How many operations per second?
- **Consistency:** How quickly must data sync across nodes?
- **Availability:** Can your agent tolerate temporary HTPC downtime?

**Example (Recruiter Agent):**
```yaml
Performance Requirements:
  Local Reads: < 10ms (for UI responsiveness)
  Local Writes: < 50ms (user can wait briefly)
  HTPC Sync: < 200ms (acceptable for network visibility)
  Query Response: < 100ms (for search results)
  HTPC Downtime Tolerance: Yes (can operate locally)
```

---

## Implementation Guidelines

### Step 1: Define Your Schema

Create a clear database schema for your agent's data:

```sql
-- Example: Recruiter Agent Schema

CREATE TABLE candidates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    skills TEXT,  -- JSON array
    experience_years INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE interviews (
    id TEXT PRIMARY KEY,
    candidate_id TEXT REFERENCES candidates(id),
    interviewer_agent TEXT,
    scheduled_date TIMESTAMP,
    notes TEXT,
    outcome TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_candidates_skills ON candidates(skills);
CREATE INDEX idx_interviews_candidate ON interviews(candidate_id);
```

### Step 2: Implement Local Storage

Set up your SQLite database with WAL mode:

```python
import sqlite3
from pathlib import Path

class AgentStorage:
    def __init__(self, agent_id: str, data_dir: Path):
        self.agent_id = agent_id
        self.db_path = data_dir / f"{agent_id}.db"
        self.conn = None
        self._initialize()
    
    def _initialize(self):
        """Initialize SQLite database with WAL mode"""
        self.conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False
        )
        # Enable WAL mode for better concurrency
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._create_tables()
    
    def _create_tables(self):
        """Create your agent's tables"""
        # Execute your CREATE TABLE statements here
        pass
```

### Step 3: Implement Dual-Write Logic

Ensure data is written to both local cache and HTPC:

```python
import httpx
import json

class AgentStorage:
    def __init__(self, agent_id: str, data_dir: Path, htpc_url: str):
        self.agent_id = agent_id
        self.db_path = data_dir / f"{agent_id}.db"
        self.htpc_url = htpc_url
        self.http_client = httpx.AsyncClient(timeout=5.0)
        self._initialize()
    
    async def write_data(self, table: str, data: dict):
        """Dual-write: local cache + HTPC"""
        # 1. Write to local SQLite
        await self._write_local(table, data)
        
        # 2. Write to HTPC (non-blocking)
        try:
            await self._write_htpc(table, data)
        except Exception as e:
            # Log error but don't fail the operation
            print(f"HTPC write failed: {e}")
            # Data is still in local cache
    
    async def _write_local(self, table: str, data: dict):
        """Write to local SQLite database"""
        # Your SQLite INSERT logic here
        pass
    
    async def _write_htpc(self, table: str, data: dict):
        """Write to HTPC via HTTP API"""
        endpoint = f"{self.htpc_url}/relay/immediate"
        payload = {
            "agent_id": self.agent_id,
            "table": table,
            "data": data,
            "timestamp": time.time()
        }
        response = await self.http_client.post(endpoint, json=payload)
        response.raise_for_status()
```

### Step 4: Implement Network Query Interface

Allow other agents to query your data:

```python
class AgentStorage:
    async def query_network(self, query: str, params: dict = None):
        """Query data from HTPC (network-wide view)"""
        endpoint = f"{self.htpc_url}/relay/query"
        payload = {
            "agent_id": self.agent_id,
            "query": query,
            "params": params or {}
        }
        response = await self.http_client.post(endpoint, json=payload)
        return response.json()
    
    async def query_local(self, query: str, params: tuple = None):
        """Query data from local cache (fast)"""
        cursor = self.conn.cursor()
        cursor.execute(query, params or ())
        return cursor.fetchall()
```

### Step 5: Handle HTPC Downtime

Ensure your agent can operate when HTPC is unavailable:

```python
class AgentStorage:
    async def write_data(self, table: str, data: dict):
        """Dual-write with fallback"""
        # Always write locally first
        await self._write_local(table, data)
        
        # Try HTPC write with timeout
        try:
            await asyncio.wait_for(
                self._write_htpc(table, data),
                timeout=2.0
            )
        except asyncio.TimeoutError:
            # Queue for later sync
            await self._queue_for_sync(table, data)
        except Exception as e:
            print(f"HTPC unavailable: {e}")
            await self._queue_for_sync(table, data)
    
    async def _queue_for_sync(self, table: str, data: dict):
        """Queue data for later HTPC sync"""
        # Store in local sync queue
        self.conn.execute(
            "INSERT INTO sync_queue (table, data, queued_at) VALUES (?, ?, ?)",
            (table, json.dumps(data), time.time())
        )
        self.conn.commit()
```

---

## Best Practices

### 1. **Use WAL Mode**
Always enable WAL mode for SQLite to prevent locking issues:
```python
conn.execute("PRAGMA journal_mode=WAL")
```

### 2. **Index Your Queries**
Create indexes for frequently queried columns:
```sql
CREATE INDEX idx_candidates_skills ON candidates(skills);
```

### 3. **Batch HTPC Writes When Appropriate**
For bulk operations, use the batch endpoint:
```python
async def batch_write(self, records: list):
    # Write all to local first
    for record in records:
        await self._write_local(record['table'], record['data'])
    
    # Send batch to HTPC
    endpoint = f"{self.htpc_url}/relay/batch"
    await self.http_client.post(endpoint, json={'records': records})
```

### 4. **Implement Health Checks**
Monitor your storage system:
```python
async def health_check(self):
    """Check storage health"""
    return {
        "local_db": self._check_local_db(),
        "htpc_connection": await self._check_htpc(),
        "sync_queue_size": self._get_sync_queue_size()
    }
```

### 5. **Plan for Data Migration**
Design your schema with versioning:
```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## Storage File Organization

### Generic Storage (Used by ALL agents)
**Location:** `commander_os/storage/`
- `base_storage.py` - Core storage functionality
- `agent_storage.py` - Simple key-value storage

### Agent-Specific Storage
**Location:** `commander_os/agents/<agent_name>/`
- `<agent_name>_storage.py` - Custom schema for that specific agent

**Examples:**
- `commander_os/agents/commander/commander_storage.py` - The Commander's storage
- `commander_os/agents/recruiter/recruiter_storage.py` - Recruiter's storage
- `commander_os/agents/<your_agent>/<your_agent>_storage.py` - Your agent's storage

**Important:** Each agent gets its own storage file named after the agent. Don't use generic names like `storage.py` - that's confusing!

## Example: Complete Recruiter Agent Storage

Here's a complete example for the Gillsystems-Recruiter-Agent:

```python
from pathlib import Path
import sqlite3
import httpx
import asyncio
import json
import time
from typing import Dict, List, Optional

class RecruiterAgentStorage:
    """Storage system for Gillsystems-Recruiter-Agent"""
    
    def __init__(self, data_dir: Path, htpc_url: str):
        self.agent_id = "gillsystems-recruiter-agent"
        self.data_dir = data_dir
        self.db_path = data_dir / f"{self.agent_id}.db"
        self.htpc_url = htpc_url
        self.conn = None
        self.http_client = httpx.AsyncClient(timeout=5.0)
        self._initialize()
    
    def _initialize(self):
        """Initialize storage system"""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._create_schema()
    
    def _create_schema(self):
        """Create database schema"""
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                skills TEXT,
                experience_years INTEGER,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS interviews (
                id TEXT PRIMARY KEY,
                candidate_id TEXT REFERENCES candidates(id),
                interviewer_agent TEXT,
                scheduled_date TIMESTAMP,
                notes TEXT,
                outcome TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                data TEXT,
                queued_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_candidates_skills 
                ON candidates(skills);
            CREATE INDEX IF NOT EXISTS idx_candidates_status 
                ON candidates(status);
            CREATE INDEX IF NOT EXISTS idx_interviews_candidate 
                ON interviews(candidate_id);
        """)
        self.conn.commit()
    
    async def add_candidate(self, candidate: Dict) -> str:
        """Add a new candidate (dual-write)"""
        candidate_id = candidate.get('id') or self._generate_id()
        candidate['id'] = candidate_id
        
        # Local write
        self.conn.execute("""
            INSERT INTO candidates (id, name, email, skills, experience_years)
            VALUES (?, ?, ?, ?, ?)
        """, (
            candidate_id,
            candidate['name'],
            candidate.get('email'),
            json.dumps(candidate.get('skills', [])),
            candidate.get('experience_years', 0)
        ))
        self.conn.commit()
        
        # HTPC write
        await self._write_to_htpc('candidates', candidate)
        
        return candidate_id
    
    async def search_candidates(self, skills: List[str]) -> List[Dict]:
        """Search for candidates by skills"""
        # Query local cache for speed
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, name, email, skills, experience_years, status
            FROM candidates
            WHERE status = 'active'
        """)
        
        results = []
        for row in cursor.fetchall():
            candidate_skills = json.loads(row[3])
            if any(skill in candidate_skills for skill in skills):
                results.append({
                    'id': row[0],
                    'name': row[1],
                    'email': row[2],
                    'skills': candidate_skills,
                    'experience_years': row[4],
                    'status': row[5]
                })
        
        return results
    
    async def _write_to_htpc(self, table: str, data: Dict):
        """Write data to HTPC with error handling"""
        try:
            endpoint = f"{self.htpc_url}/relay/immediate"
            payload = {
                "agent_id": self.agent_id,
                "table": table,
                "data": data,
                "timestamp": time.time()
            }
            await self.http_client.post(endpoint, json=payload)
        except Exception as e:
            # Queue for later sync
            self.conn.execute(
                "INSERT INTO sync_queue (table_name, data) VALUES (?, ?)",
                (table, json.dumps(data))
            )
            self.conn.commit()
    
    def _generate_id(self) -> str:
        """Generate unique ID"""
        import uuid
        return str(uuid.uuid4())
    
    async def close(self):
        """Clean up resources"""
        if self.conn:
            self.conn.close()
        await self.http_client.aclose()
```

---

## Testing Your Storage

Always test your storage implementation:

```python
import pytest
import asyncio
from pathlib import Path

@pytest.mark.asyncio
async def test_dual_write():
    """Test that data is written to both local and HTPC"""
    storage = RecruiterAgentStorage(
        data_dir=Path("./test_data"),
        htpc_url="http://localhost:8000"
    )
    
    candidate = {
        "name": "John Doe",
        "email": "john@example.com",
        "skills": ["Python", "SQL"],
        "experience_years": 5
    }
    
    candidate_id = await storage.add_candidate(candidate)
    assert candidate_id is not None
    
    # Verify local write
    results = await storage.search_candidates(["Python"])
    assert len(results) > 0
    assert results[0]['name'] == "John Doe"
    
    await storage.close()
```

---

## Troubleshooting

### Issue: Slow Query Performance
**Solution:** Add indexes for frequently queried columns
```sql
CREATE INDEX idx_column_name ON table_name(column_name);
```

### Issue: HTPC Sync Failures
**Solution:** Check sync queue size and process backlog
```python
async def process_sync_queue(self):
    cursor = self.conn.cursor()
    cursor.execute("SELECT id, table_name, data FROM sync_queue LIMIT 100")
    for row in cursor.fetchall():
        await self._write_to_htpc(row[1], json.loads(row[2]))
        self.conn.execute("DELETE FROM sync_queue WHERE id = ?", (row[0],))
    self.conn.commit()
```

### Issue: Database Locked
**Solution:** Ensure WAL mode is enabled
```python
result = self.conn.execute("PRAGMA journal_mode").fetchone()
assert result[0] == 'wal'
```

---

## Summary

When designing storage for your Commander OS agent:

1. ✅ **Start Local** - Use SQLite with WAL mode for fast local operations
2. ✅ **Think Network** - Design for cluster-wide visibility from day one
3. ✅ **Dual-Write** - Write to both local and HTPC for real-time consistency
4. ✅ **Handle Failures** - Queue data when HTPC is unavailable
5. ✅ **Index Smartly** - Optimize for your query patterns
6. ✅ **Test Thoroughly** - Validate both local and network operations

Your agent's storage is critical to its effectiveness. Take time to design it well!

---

## Additional Resources

- [SQLite WAL Mode Documentation](https://sqlite.org/wal.html)
- [Commander OS Storage Architecture](./STORAGE_ARCHITECTURE.md)
- [Commander OS Developer Guide](./DEVELOPER_GUIDE.md)

---

**Questions or Issues?**  
Open an issue on the Commander OS repository or consult the community forum.
