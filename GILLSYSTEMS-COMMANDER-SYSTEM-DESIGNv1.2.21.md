# **Gillsystems Commander OS: System Operating Architecture v1.2.21**

**Last Updated:** 2026-01-06  
**Version:** 1.2.21 (Unified Cluster Memory & Agent Mobilization)  
**Status:** Phases 1-6 Complete. Phase 7 (Storage Integration) Initialized.

---

## **Cluster Topology (Authoritative)**

| Node | Host / Port | Role | Description |
|------|-------------|------|-------------|
| **Gillsystems-Main** | `10.0.0.164:8000` | Orchestrator | Runs The Commander meta-agent and System Manager. |
| **Gillsystems-HTPC** | `10.0.0.42:8001` | Storage/Relay | Central Dataset authority and primary message relay node. |
| **Gillsystems-Laptop** | `10.0.0.93:8002` | Worker | Model server and agent execution environment. |
| **Gillsystems-Steam-Deck** | `10.0.0.139:8003` | Worker | Model server and agent execution environment. |

---

## **Storage Architecture (ZFS)**

The HTPC node hosts the authoritative dataset for the entire cluster.
- **Root Path:** `/gillsystems_zfs_pool/AI_storage`
- **Subdirectories:**
  - `/logs`: Aggregated system and agent logs.
  - `/artifacts`: Generated files and work products.
  - `/checkpoints`: Saved model states and agent weights.
  - `/memory`: `commander_memory.db` (The single source of truth for persistent context).
  - `/relay`: Shared message routing state.
  - `/agents`: Persisted agent configurations.

---

## **Commander Protocol Layer**

To ensure architectural integrity and prevent drift, all communication follows the **Commander Protocol**.

### **1. The Commander (Meta-Agent)**
- Authoritative orchestrator.
- Responsible for task definition, context injection, and role enforcement.
- Absolute priority in all routing.

### **2. Message Enveloping**
- Every transmission is wrapped in a `MessageEnvelope`:
  - `id`: Unique UUID.
  - `timestamp`: Unix epoch.
  - `msg_type`: COMMAND, RESPONSE, QUERY, EVENT, ERROR, HEARTBEAT.
  - `sender_id` / `recipient_id`: Authoritative node/agent identifiers.
  - `task_id`: Traceability for complex multi-agent workflows.
  - `payload`: Data or instructions.

---

## **Memory System & SQL Flexibility**

Gillsystems Commander OS uses a persistent memory system backed by **SQLite** through the **SQLAlchemy ORM**.

### **Is the database flexible?**
**Yes.** The system is designed for unlimited horizontal expansion:
1. **Metadata JSON Column:** The `MessageModel` includes a `metadata_json` field. This allows the Commander to store arbitrary key-value extensions (e.g., sentiment analysis, token counts, reasoning traces) without requiring a structural database migration.
2. **Typed BLOBs:** Content is stored as compressed `LargeBinary` blobs, allowing for multi-modal context (large text blocks, code snippets, or encoded artifacts) to be stored efficiently.
3. **Task-Specific Indexing:** The schema provides deep indexing on `task_id`, allowing the system to scale to thousands of simultaneous tasks while maintaining sub-millisecond context retrieval.
4. **Pluggable Architecture:** While SQLite is the current default for performance and ease of ZFS portability, SQLAlchemy allows the system to switch to PostgreSQl or MariaDB if the event volume grows beyond local file locking capabilities.

---

## **Directory Structure**

```
The-Commander-Agent/
├── commander_os/                  # Core OS code
│   ├── core/
│   │   ├── system_manager.py      # Authoritative Orchestrator
│   │   ├── protocol.py            # Commander Protocol Definitions
│   │   ├── memory.py              # Extensible MessageStore
│   │   └── ...
│   └── interfaces/
│       └── rest_api.py            # FastAPI Interface
├── config/
│   ├── relay.yaml                 # Aligned Cluster Topology
│   └── roles.yaml                 # Agent Hierarchy (Commander Priority)
└── tests/                         # Full coverage suite (61+ tests)
```

---

*Property of Gillsystems. Alignment is Mandatory.*
