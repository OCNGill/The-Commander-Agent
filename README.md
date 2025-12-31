# The-Commander: AI Agent Operating System

**The-Commander** is a distributed orchestrator for managing a cluster of heterogeneous AI agents. It centralizes state, memory, and task lifecycle management while allowing decentralized execution across multiple compute nodes.

---

## **Architecture Overview**

The-Commander follows a strict generic protocol where a central "Commander" meta-agent directs subordinate agents (Architect, Coder, Reasoner, Synthesizer) to achieve complex goals.

### **Cluster Topology (Authoritative)**

| Node | IP | Role | Description |
|------|----|------|-------------|
| **Main** | `10.0.0.164:8000` | Orchestrator | Runs the core System Manager and Commander logic. |
| **HTPC** | `10.0.0.42:8001` | Relay/Storage | Central message relay and ZFS persistent storage (`/gillsystems_zfs_pool/AI_storage`). |
| **Laptop** | `10.0.0.93:8002` | Worker | Local compute node. |
| **SteamDeck** | `10.0.0.139:8003` | Worker | Auxiliary compute node. |

---

## **Quick Start (Developer Mode)**

### **Prerequisites**
- Python 3.10+
- `pip install -r requirements.txt` (or manually: `fastapi uvicorn textual httpx sqlalchemy pyyaml pydantic`)

### **Running Tests**
Verify the integrity of the Protocol Layer and Core Managers:
```bash
python -m pytest tests/ -v
```

### **Manual Launch (API)**
To start the Main Node REST Interface:
```bash
uvicorn commander_os.interfaces.rest_api:app --host 0.0.0.0 --port 8000
```

---

## **Project Structure**

```
The-Commander-Agent/
├── commander_os/
│   ├── core/              # Core Logic
│   │   ├── system_manager.py  # Orchestrator
│   │   ├── protocol.py        # Comm Standard (Envelopes, Tasks)
│   │   ├── memory.py          # SQLite/ZFS Storage
│   │   └── ...
│   └── interfaces/        # External Access
│       └── rest_api.py        # FastAPI Headers
├── config/
│   ├── relay.yaml         # Topology Config
│   └── roles.yaml         # Agent Hierarchy
└── tests/                 # 100% Coverage Test Suite
```

## **Status (v1.2.0)**
- **Phase 1-3 Complete**: Core Managers, Memory, API.
- **Current Focus**: Protocol Layer Integration.
- **Paused**: TUI / Web GUI / Launchers.

---

*Property of Gillsystems.*
