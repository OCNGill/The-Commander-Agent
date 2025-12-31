# **The-Commander: System Operating Architecture v1.1.0**

**Last Updated:** 2025-12-30  
**Version:** 1.1.0 (Added persistent message memory system)  
**Previous:** [v1.0.0](./THE-COMMANDER-SYSTEM-DESIGNv1.0.0.md)

---

## **Overview**

The-Commander is a **multi-interface orchestration system** for managing a heterogeneous cluster of local AI models running on distributed AMD hardware. It provides unified control and monitoring across **system lifecycle**, **node management**, **agent coordination**, and **model configuration**.

---

## **Core Command Set**

### **System Level**
- `start` — Bootstrap entire Commander cluster (relay + all nodes + all agents)
- `stop` — Graceful shutdown of all nodes/agents
- `status` — System-wide health and state

### **Node Level**
- `start <node_id>` — Launch specific node
- `stop <node_id>` — Shutdown specific node
- `status <node_id>` — Node health, connected agents, resource usage

### **Agent Level (per node)**
- `start <node_id> <agent_id>` — Launch agent on node
- `stop <node_id> <agent_id>` — Shutdown agent
- `status <node_id> <agent_id>` — Agent state, current role, model info

### **Agent Configuration**
- `config <agent_id> --model <model_path>` — Change model
- `config <agent_id> --context-size <size>` — Modify context window
- `config <agent_id> --ngl <layers>` — GPU layer count
- `config <agent_id> --fa [true|false]` — Flash attention toggle
- `config <agent_id> --addr <ip:port>` — Network endpoint
- `config <agent_id> --role [architect|coder|reasoner|synthesizer]` — Set/override role

### **Extended Set: Llama.cpp Commands**
- Pass-through support for Llama.cpp CLI parameters:
  - `--threads`, `--batch`, `--ubatch`, `--temp`, `--top-k`, `--top-p`, `--repeat-penalty`, etc.
  - Exposed via `config <agent_id> --llama-param <key> <value>`

---

## **Multi-Interface Architecture**

### **1. REST API (FastAPI)**
- Machine-readable endpoints for all operations
- Real-time state queries
- Configuration CRUD
- Event webhooks (optional)

### **2. Terminal UI (TUI)**
- Real-time monitoring dashboard
- Live agent/node status
- Keyboard-driven control
- Built with Textual

### **3. Web GUI (Browser)**
- Graphical system control
- Agent configuration interface
- Historical logs and metrics
- Auto-opens on launch (optional)

---

## **Configuration Model**

### **Static (Relay)**
- `config/relay.yaml` — Network topology, relay port, node endpoints (immutable during runtime)

### **Dynamic (Agent)**
- `config/agents/<agent_id>.yaml` — Per-agent model, context, NGL, FA, role, etc. (hot-reloadable)
- `config/roles.yaml` — Role definitions and override permissions

---

## **One-Shot Executable Launchers**

### **Linux: `commander_launcher.sh`**
- Detects environment (native/WSL)
- Bootstraps relay + node services in background (nohup)
- Launches TUI/Web GUI in foreground
- Single execution: `./commander_launcher.sh`

### **Windows: `commander_launcher.bat`**
- Detects Python + Llama.cpp availability
- Launches relay + services (detached)
- Opens Web GUI in default browser
- Single execution: `commander_launcher.bat`

---

## **Directory Structure**

```
The-Commander-Agent/
├── commander_os/                  # Core system
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config_manager.py      # YAML loading, validation
│   │   ├── system_manager.py      # System lifecycle
│   │   ├── node_manager.py        # Node lifecycle
│   │   ├── agent_manager.py       # Agent lifecycle
│   │   └── state.py               # In-memory system state
│   ├── interfaces/
│   │   ├── __init__.py
│   │   ├── rest_api.py            # FastAPI server
│   │   ├── tui.py                 # Textual TUI
│   │   └── web_gui.py             # Web interface
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       ├── llama_cpp_bridge.py    # Llama.cpp CLI wrapper
│       └── memory.py              # Persistent message memory system
├── memory/
│   ├── commander_memory.db        # SQLite persistent message store
│   └── archive/                   # Archived message backups
├── config/
│   ├── relay.yaml                 # Static relay config
│   ├── roles.yaml                 # Role definitions
│   └── agents/
│       ├── default.yaml
│       ├── htpc.yaml
│       └── ...
├── scripts/
│   ├── commander_launcher.sh       # Linux one-shot launcher
│   ├── commander_launcher.bat      # Windows one-shot launcher
│   └── bootstrap.py               # Shared bootstrap logic
├── relay/
│   └── relay_server.py            # Message routing hub
├── logs/
│   ├── system.log
│   ├── relay/
│   └── agents/
└── The-Commander-Agent.code-workspace
```

---

## **State Persistence**

- **Agent configs**: YAML files (survives restart)
- **Runtime state**: In-memory (reset on restart, can be persisted to SQLite if needed)
- **Role assignments**: Persistent in agent YAML, user-overridable anytime

---

## **Persistent Message Memory System**

### **Design Goals**
- ✅ **Complete audit trail** — Every inter-agent communication logged
- ✅ **Minimal storage** — Compressed, deduplicated, summarized
- ✅ **Fast retrieval** — Indexed for agent queries and historical context
- ✅ **Agent learning** — Persistent memory agents can query for decision-making

### **Architecture**

#### **1. Message Capture Layer**
- All relay-routed messages intercepted and logged
- Metadata captured: timestamp, sender, recipient(s), role, task_id, iteration
- Message content stored with schema validation

#### **2. Storage Backend: SQLite**
- Single `commander_memory.db` file (persistent)
- Structured tables:
  - `messages` — Raw message logs (indexed by sender, recipient, timestamp, task_id)
  - `message_summaries` — Compressed abstracts (one per task/phase)
  - `agent_interactions` — Flattened view for fast queries
  - `memory_index` — Searchable tags, keywords, topics

#### **3. Compression Strategy**
- **Message deduplication** — Identical messages logged once, reference-counted
- **Summarization** — After task completion, create executive summary (10% of original size)
- **Archival** — Messages older than N days moved to separate archive table
- **Gzip compression** — Message bodies compressed before storage
- **Bloom filters** — Fast negative lookups for duplicate detection

#### **4. Memory Query Interface**
- Agents can query persistent memory via REST endpoint:
  - `GET /memory/search?task_id=X` — All messages for task X
  - `GET /memory/agent?sender=architect&recipient=coder` — Interaction patterns
  - `GET /memory/summary?task_id=X` — Executive summary for context window
  - `GET /memory/similar?content=...` — Find similar past exchanges
- Responses paginated for efficient memory usage

#### **5. Compaction Job**
- Runs daily (configurable):
  - Summarize completed tasks
  - Archive old messages
  - Rebuild indexes
  - Defragment database
- Reduces disk footprint while preserving queryability

#### **6. Audit Trail Logging**
- Every operation logged: message received, stored, summarized, queried
- Traceback: which agent triggered which memory query
- Full lineage: decision → supporting memory query → past context used

### **Storage Footprint Example**

**Before compression:**
- 1000 agent messages over 24 hours: ~5-10 MB (raw JSON)

**After compression:**
- Raw messages: ~2 MB (gzip)
- Deduplicated: ~1.5 MB
- Summary only: ~500 KB
- **Total with index: ~1 MB**

### **Integration Points**

1. **Relay intercepts all messages** → logs to memory system
2. **Agent makes decision** → queries persistent memory for context
3. **Task completes** → system summarizes and archives
4. **TUI/Web GUI displays** → memory stats, audit trail, query interface
5. **REST API exposes** → agents can query memory programmatically

---

## **Execution Flow**

1. **User runs launcher** (`commander_launcher.sh` or `commander_launcher.bat`)
2. **Bootstrap script**:
   - Loads `config/relay.yaml`
   - Starts relay server (background)
   - Starts node managers (background)
   - Starts agent processes (background)
   - Launches TUI or Web GUI (foreground)
3. **User controls system** via any interface (REST API, TUI, Web GUI simultaneously)
4. **System manages state**: All commands route through core managers → config changes → relay broadcasting

---

## **Key Design Principles**

✅ **Unified control** — All interfaces (CLI-like, TUI, REST, Web) control same system  
✅ **Stateless nodes** — Nodes are ephemeral; state lives in config files  
✅ **Hot-reloadable configs** — Agent configs update without restart  
✅ **Role flexibility** — User can override agent roles anytime  
✅ **Audit trail** — All operations logged with timestamps  
✅ **Llama.cpp transparency** — Full parameter passthrough support  
✅ **Production-ready** — Error handling, retries, graceful degradation  

---

## **Success Criteria**

✅ Single `.bat`/`.sh` execution launches entire system  
✅ REST API provides full lifecycle + config control  
✅ TUI shows real-time node/agent status  
✅ Web GUI allows easy agent configuration  
✅ Agent configs persist and survive restart  
✅ Role assignments can be overridden by user  
✅ Llama.cpp parameters fully exposed and configurable  
✅ Relay routes all inter-agent messages correctly  

---

## **Next Steps**

1. Create core managers (ConfigManager, SystemManager, NodeManager, AgentManager)
2. Implement REST API (FastAPI)
3. Build TUI dashboard (Textual)
4. Build Web GUI
5. Create launcher scripts (.bat / .sh)
6. Integration testing across all interfaces
