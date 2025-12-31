# **The-Commander — 2:30 AM Master Plan (v1.2.1)**

**Date:** 2025-12-31 02:30  
**Status:** Phases 1–3 Complete | **Protocol Layer Active**  
**Authoritative State:** Realignment to Authoritative Compute Benchmarks & HTPC Environment.

---

## **1. Project Overview & Objective**

The Commander is a **rigorous, multi-model orchestration layer** designed to coordinate a heterogeneous cluster of local AI models via a standardized **Collaboration Protocol**. Built on **7D Agile principles**, it manages a team of specialized models to co-design solutions with full **traceability**, **reproducibility**, and **local-only data security**.

---

## **2. Authoritative Architecture & Topology**

### **Cluster Nodes & Performance Benchmarks**
The system is weighted to prioritize high-compute nodes for core reasoning and implementation.

| Node ID | Network Address | Hostname | Hardware | t/s | Role Assignment |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **node-main** | `http://10.0.0.164:8000/` | Gillsystems-Main | Radeon 7900XTX | **130** | Orchestrator + Heavy Compute |
| **node-htpc** | `http://10.0.0.42:8001/` | Gillsystems-HTPC | Radeon 7600 | **60** | Relay Hub + Storage + Worker |
| **node-steamdeck**| `http://10.0.0.139:8003/`| Steam Deck | Custom APU | **30** | Tertiary Worker (Light Jobs) |
| **node-laptop**| `http://10.0.0.93:8002/` | Laptop | Integrated/Mobile | **9** | Tertiary Worker (Minimal Load) |

### **HTPC Storage (Single Source of Truth)**
All nodes interact with the HTPC dataset root: `/gillsystems_zfs_pool/AI_storage/`
- **HTPC User Context**: `gillsystems-htpc@Gillsystems-HTPC`
- **HTPC Installation Path**: `/home/gillsystems-htpc/`
- **Subdirectories**:
  - `/logs`: Aggregated system/agent logs.
  - `/artifacts`: Traceable work products.
  - `/memory/commander_memory.db`: SQLite persistent message store.
  - `/checkpoints`: Versioned model states and weights.

---

## **3. Commander Protocol (The Execution Standard)**

All inter-node traffic MUST be wrapped in the **Protocol Envelope** (`protocol.py`):
- **MessageEnvelope**: UUID, Timestamp, Sender/Recipient, Task ID, Priority, GZIP Payload.
- **TaskDefinition**: Authoritative unit of work with assigned roles and dependencies.
- **Priority Scaling**: Commander logic will automatically route Architect/Coder tasks to Main/HTPC based on the performance benchmarks above.

---

## **4. Current Build Status**

### **✅ Core Managers & Memory**
- **System/Node/Agent Managers**: Complete.
- **Memory Store**: SQLite + Metadata flexibility implemented.
- **REST API**: Operational cluster-wide.

### **✅ Protocol Layer**
- `protocol.py` defined and unit-tested (61 tests total passing).
- **Role Hierarchy**: Commander (0) -> Architect (1) -> Coder/Reasoner (2) -> Synthesizer (3).

---

## **5. Launcher & Deployment Strategy**

### **HTPC Node Setup**
- **User**: `gillsystems-htpc`
- **Folders**: `~/relay`, `~/agents`, `~/scripts` (under `/home/gillsystems-htpc/`).
- **Daemon**: `~/scripts/htpc_start.sh` (nohup management).
- **Desktop Shortcut Update**:
  - Old: `/home/gillsystems-htpc/AI/robot/Gillsystems-HTPC-LLM-Server-Port-8001.sh`
  - **New**: `/home/gillsystems-htpc/scripts/htpc_start.sh`

---

## **6. The Road to MVP (Next Steps)**

### **Phase 4: Protocol Integration (Current Focus)**
- [ ] **Agent Wrap**: Update `AgentManager` to enforce `MessageEnvelope`.
- [ ] **Load Balancing**: Inject the Benchmark logic into the `SystemManager` to prioritize `node-main` and `node-htpc`.
- [ ] **Relay Client**: Implement HTPC push logic for distributed envelopes.
- [ ] **Commander "Snap-Back"**: Logic to enforce role-discipline across the cluster.

### **Future Phases**
- **Phase 5**: TUI Dashboard (Real-time cluster monitoring).
- **Phase 6**: Web GUI (Interactive configuration & memory browser).

---

## **7. Documentation & Alignment**
- [x] **README.md** Updated.
- [x] **System Design** v1.2.0 Sync complete.
- [x] **Diagrams** v1.2.0 Sync complete.
- [x] **Master Plan (2am.md)** Aligned to benchmarks and HTPC user environment.
