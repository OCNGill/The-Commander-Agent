# Storage Architecture: High-Performance Local Cache + Lightweight HTPC Sync

**Version:** 1.2.21  
**Focus:** Speed, Longevity, Knowledge Corpus

---

## **Design Philosophy**

The Commander OS storage system is built around **three core principles**:

1. **Performance First**: Local NVMe acts as the primary working memory for agents (step down from DDR). Agents read/write at full disk speed with zero latency for their own operations.
2. **Immediate Network Visibility**: All writes are **simultaneously pushed to HTPC** so data is visible cluster-wide instantly. You can access agent output from any node with <10ms latency.
3. **Longevity & Persistence**: HTPC provides the durable, centralized knowledge corpus. All cluster intelligence is preserved for long-term analysis.

**Critical Use Case**: You may be working from Main while agents run on Laptop/Steam Deck. The dual-write pattern ensures you see their output immediately without waiting for async sync delays.

**Out of Scope**: Model file storage/management. The OS reads available models from user-specified directories. Model storage is the end user's responsibility.

---

## **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    AGENT NODE (Local)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Local NVMe Cache (Fast Working Memory)                │ │
│  │  • SQLite WAL mode (compressed messages)               │ │
│  │  • Size: Role + Context Window aware                   │ │
│  │  • Agent reads locally (sub-ms)                        │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓ (writes to both)                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Outbox Queue (Retry on HTPC Failure)                  │ │
│  │  • Persistent SQLite table                             │ │
│  │  • Guaranteed delivery with exponential backoff        │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                  ↓ (IMMEDIATE write-through)
┌─────────────────────────────────────────────────────────────┐
│              HTPC (Gillsystems-HTPC)                         │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  Relay HTTP API (Network-Wide Access Point)            │ │
│  │  • POST /sync/message (immediate single write)         │ │
│  │  • POST /sync/messages (batch for retries)             │ │
│  │  • GET /query/messages (paginated search)              │ │
│  │  • Data visible to ALL nodes instantly (<10ms)         │ │
│  └────────────────────────────────────────────────────────┘ │
│                           ↓                                   │
│  ┌────────────────────────────────────────────────────────┐ │
│  │  ZFS Dataset: Knowledge Corpus (Network-Accessible)    │ │
│  │  • /gillsystems_zfs_pool/AI_storage/messages/          │ │
│  │  • SQLite (primary) + compressed archives              │ │
│  │  • Immediate writes, low I/O (indexed inserts)         │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
           ↑ (all nodes query here for cluster-wide data)
```

---

## **Local Cache Sizing (Role + Context Aware)**

Cache size is calculated based on:
- **Agent Role**: Workload type (e.g., Recruiter = high write volume, Commander = low)
- **Model Context Window**: Larger context = more messages in working memory

### **Sizing Formula**
```
cache_bytes = BASE_SIZE + (CONTEXT_TOKENS / 1000) * SCALE_FACTOR
```

### **Recommended Defaults**

| Agent Role | Base Size | Context Window | Scale Factor | Total Cache |
|------------|-----------|----------------|--------------|-------------|
| **Commander** (Meta-Agent) | 100 MB | 32k | 0.5 MB/1k tokens | ~116 MB |
| **Recruiter** (Scraper/Writer) | 2 GB | 32k | 2 MB/1k tokens | ~2.06 GB |
| **Reasoner** (Analysis) | 500 MB | 128k | 1 MB/1k tokens | ~628 MB |
| **Coder** (File I/O Heavy) | 1 GB | 64k | 1.5 MB/1k tokens | ~1.09 GB |
| **Synthesizer** (Aggregator) | 300 MB | 32k | 0.75 MB/1k tokens | ~324 MB |

**Override**: User can manually set `cache_max_bytes` in agent config YAML.

---

## **Local Storage Implementation**

### **Primary Store: SQLite (WAL Mode)**
- **File**: `<node_data_dir>/cache/<agent_id>/messages.db`
- **Schema**:
  ```sql
  CREATE TABLE messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      msg_id TEXT UNIQUE NOT NULL,
      timestamp REAL NOT NULL,
      task_id TEXT,
      sender TEXT,
      recipient TEXT,
      role TEXT,
      content BLOB,  -- GZIP compressed JSON
      synced INTEGER DEFAULT 0,
      INDEX idx_task (task_id),
      INDEX idx_timestamp (timestamp),
      INDEX idx_synced (synced)
  );
  ```
- **Write Path**: Agent → Local SQLite (instant)
- **Read Path**: Agent reads from local cache first (sub-millisecond)

### **Outbox Queue (Async Upload)**
- **File**: `<node_data_dir>/cache/<agent_id>/outbox.db`
- **Schema**:
  ```sql
  CREATE TABLE outbox (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      batch_id TEXT UNIQUE NOT NULL,
      payload BLOB,  -- GZIP compressed batch
      created_at REAL,
      status TEXT DEFAULT 'pending',  -- pending, sending, acked, failed
      retry_count INTEGER DEFAULT 0,
      last_attempt REAL
  );
  ```
- **Uploader**: Background thread that:
  1. Reads pending batches (every 5s or when queue > 100 messages)
  2. POSTs to HTPC `/sync/messages`
  3. On ACK: marks batch as `synced=1` in local messages table
  4. On failure: exponential backoff, retry

---

## **HTPC Sync Layer (Lightweight)**

### **Relay Endpoints**
- **POST /sync/message** (singular, immediate)
  - Payload: Single `MessageEnvelope` JSON
  - Action: Immediate insert to HTPC SQLite (<5ms)
  - Response: `{"status": "stored", "msg_id": "<uuid>"}`
  - **This is the primary write path for network-wide visibility**

- **POST /sync/messages** (batch, for retry queue)
  - Payload: `{"batch_id": "<uuid>", "node_id": "<node>", "messages": [...]}`
  - Action: Batch insert to HTPC SQLite
  - Response: `{"status": "acked", "batch_id": "<uuid>"}`
  - Used by outbox uploader for failed/queued writes

- **GET /query/messages**
  - Query params: `?agent=<id>&task=<id>&since=<timestamp>&limit=100`
  - Action: Paginated query from HTPC SQLite
  - Response: `{"messages": [...], "total": 1234, "page": 1}`
  - **Any node can query cluster-wide data instantly**

- **POST /sync/files**
  - Payload: Multipart file upload
  - Action: Save to `/gillsystems_zfs_pool/AI_storage/files/<agent_id>/`
  - Response: `{"status": "stored", "file_id": "<uuid>"}`

### **HTPC Storage (SQLite on ZFS)**
- **File**: `/gillsystems_zfs_pool/AI_storage/messages/cluster_messages.db`
- **Same schema as local**, but all nodes append here
- **No ZFS snapshots during writes** (user can schedule manual snapshots via cron)
- **Memory footprint**: Minimal—SQLite uses ~10-20MB for writes, no heavy caching

---

## **Message-Based Reporting Interface**

### **Separate UI (Not Main GUI)**
- **Route**: `/messages` or `/reports`
- **Opens in**: New tab or modal overlay
- **Functionality**:
  - **Inbox View**: List of agent reports (HOT leads, errors, task completions)
  - **Filters**: By agent role, time range, priority
  - **Actions**: 
    - "Acknowledge" (mark read)
    - "Execute" (trigger follow-up task)
    - "Archive" (move to long-term storage)
  - **Search**: Full-text search across message corpus

### **Main GUI Updates**
- **Notification Badge**: Small indicator showing unread message count
- **No message content in main view**: Keep dashboard clean and tactical

---

## **Operational Flow**

### **Agent Write (Dual-Write for Immediate Network Visibility)**
1. Agent generates message
2. **Write to local SQLite cache** (instant, <1ms) — for agent's own fast reads
3. **Simultaneously POST to HTPC** (write-through, <10ms network latency) — for immediate cluster-wide visibility
4. Agent continues work (local write is non-blocking; HTPC write uses fire-and-forget with retry queue)

**Critical Design Point**: You need immediate access from any node. The dual-write ensures:
- Local agent gets instant access (NVMe speed)
- Any other node querying HTPC gets the data immediately (no sync delay)
- If HTPC write fails (network issue), it queues locally and retries

### **Write Failure Handling**
1. If HTPC POST succeeds: Mark as synced in local cache
2. If HTPC POST fails:
   - Append to outbox queue (guaranteed delivery)
   - Background uploader retries with exponential backoff
3. Local cache always succeeds (agent never blocked)

### **HTPC Receive**
1. Relay receives message (single or batch)
2. Decompress payload if needed
3. **Immediate insert** to cluster SQLite (single transaction, <5ms)
4. Return ACK
5. **Data is now visible to all nodes immediately**
6. I/O load: ~1-5 MB/s during active work (negligible on HTPC)

### **Dashboard Query (From Any Node)**
1. User opens `/messages` (from Main, Laptop, anywhere)
2. **Query HTPC SQLite directly** (over HTTP API)
3. Paginated, indexed query (fast, <50ms typical)
4. Render in separate interface
5. Actions trigger new tasks via REST API

### **Agent Read (Local-First, Fallback to HTPC)**
1. Agent queries local cache first (sub-millisecond)
2. If not found (cache miss or recent message from another agent):
   - Query HTPC via HTTP API
   - Cache result locally for future reads
3. This keeps local reads blazing fast while ensuring cluster-wide consistency

---

## **Failure Modes & Guarantees**

### **Network Partition**
- Local cache continues to grow (up to `cache_max_bytes`)
- Outbox queue accumulates
- When HTPC returns: uploader resumes, syncs backlog
- **No data loss**: All messages persist locally until ACKed

### **HTPC Unavailable**
- Agents remain fully operational (local cache)
- Sync halts, outbox grows
- Dashboard shows "Sync Lag" warning
- When HTPC returns: automatic catch-up

### **Disk Full (Local)**
- Agent logs error, stops accepting new writes
- Dashboard alert: "Node <X> cache full"
- Manual intervention: clear old messages or increase quota

### **Disk Full (HTPC)**
- Relay rejects new batches with `507 Insufficient Storage`
- Uploader retries with backoff
- Dashboard alert: "HTPC storage critical"

---

## **Configuration Schema**

### **Agent Config (`config/agents/<agent_id>.yaml`)**
```yaml
agent_id: "recruiter-001"
role: "recruiter"
node_id: "Gillsystems-Laptop"
enabled: true

cache:
  max_bytes: 2147483648  # 2 GB
  retention_days: 30
  compression: true
  
sync:
  batch_size: 500
  interval_seconds: 5
  retry_max: 10
  retry_backoff_base: 2
```

### **Node Config (`config/relay.yaml`)**
```yaml
nodes:
  - id: "Gillsystems-HTPC"
    host: "10.0.0.42"
    port: 8001
    role: "storage"
    sync_enabled: true
    sync_endpoint: "http://10.0.0.42:8001/sync/messages"
```

---

## **Metrics & Observability**

### **Exposed Metrics (Prometheus-style)**
- `cache_bytes_used{node, agent}`: Current cache usage
- `outbox_queue_depth{node, agent}`: Pending messages
- `sync_lag_seconds{node}`: Time since last successful sync
- `sync_failures_total{node}`: Cumulative sync failures
- `htpc_write_throughput_bytes`: HTPC ingestion rate

### **Dashboard Widgets (Optional)**
- Node cache usage bar charts
- Sync status indicators (green/yellow/red)
- Last sync timestamp per node

---

## **Implementation Checklist**

- [ ] Create `commander_os/core/cache_manager.py` (local cache + outbox)
- [ ] Add Relay endpoints: `/sync/messages`, `/sync/files`
- [ ] Update `ConfigManager` to load cache configs
- [ ] Implement background uploader thread
- [ ] Create `/messages` UI route (separate interface)
- [ ] Add notification badge to main GUI
- [ ] Integration tests: simulate agent writes, verify HTPC sync
- [ ] Performance tests: measure local write latency (<1ms target)
- [ ] Load tests: HTPC under sustained sync (target: <5% CPU, <50MB RAM)

---

**Status**: Design complete. Ready for implementation.
