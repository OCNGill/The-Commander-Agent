# **Gillsystems Commander OS — Master Plan (v1.2.21)**

**Date:** 2026-01-06  
**Status:** Phase 7 Initialized | **Unified Cluster Memory Convergence**  
**Authoritative State:** Command & Control Logic extending to Cluster Worker autonomy.

---

## **1. Authoritative Architecture & Topology**

### **Cluster Nodes & Hardware Calibration**
| Node ID | Physical Host | Hardware | Bench (t/s) | Model Configuration |
| :--- | :--- | :--- | :--- | :--- |
| **Gillsystems-Main** | Gillsystems-Main | Radeon 7900XTX | **130** | Qwen3-Coder-25B (131k ctx, 999 NGL) |
| **Gillsystems-HTPC** | Gillsystems-HTPC | Radeon 7600 | **60** | Granite-4.0-h-tiny (114k ctx, 40 NGL) |
| **Gillsystems-Steam-Deck**| Gillsystems-Steam-Deck | Custom APU | **30** | Granite-4.0-h-tiny (21k ctx, 32 NGL) |
| **Gillsystems-Laptop**| Gillsystems-Laptop| Integrated | **9** | Granite-4.0-h-tiny (21k ctx, 999 NGL) |

---

## **2. Build Progress (7D Agile)**

### **✅ Phase 5: TUI Dashboard & Engine Ignition**
- Real-time performance monitoring and automated hardware backend (llama.cpp) ignition.

### **🔄 Phase 6: Strategic Dashboard (DEVELOP)**
*Objective: Transform the OS into a graphical Command & Control center.*

- [x] **React/Vite Infrastructure**: Modern web dashboard foundation built with tactical design system.
- [x] **Backend Integration**: Connected the GUI to the SystemManager REST API via tactical `CommanderAPI` client.
- [x] **Real-time WebSockets**: Streaming node health and logs to the browser with zero-latency tactical broadcaster.
- [x] **Dynamic Hardware Dials**: Real-time adjustment of Context (`-c`) and NGL (`-ngl`) per node with remote re-ignition.
- [x] **Strategic Model Selector**: Remote file browser to locate and swap `.gguf` files with dedicated FA (Flash Attention) toggle.
- [x] **Binary Authority Control**: Graphical selection/renaming of backend binaries (e.g., `go.exe` vs `llama-server.exe`).
- [x] **Cluster Heartbeat**: Live visualizations of node TPS load and availability with real-time heartbeat telemetry.
- [x] **Intelligence Log**: Web-based stream of the HTPC MessageStore with tactical search and multi-layer filtering.
- [x] **One-Click Deployment**: Single "IGNITE ALL" button to spin up the entire cluster with high-fidelity progression HUD.
- [x] **Chat Interface**: Direct chat panel routed to highest-priority active agent for seamless workflow orchestration.
- [x] **Stats for Nerds**: Dedicated panel for real-time node statistics and command output.

---

## **4. Future Phases (The Road to v1.5)**

### **🔄 Phase 7: Unified Cluster Memory (ACTIVE)**
- Canonical persistence moved to HTPC Relay server over ZFS.
- Agents on all nodes report via standardized Relay protocol.

### **🔄 Phase 8: Strategic Agent Mobilization**
- Implementation of **The Commander** Meta-Agent in `commander_os/agents/commander/`.
- Deployment of the **Gillsystems-Recruiter-Agent** as the first functional sub-agent.

### **🔄 Phase 9: Tool Authority (MCP)**
- Integration of Tool Access Layer for agents to interact with files/terminals.

### **🔄 Phase 10: Cluster Synthesis**
- v1.5 Release: High-fidelity multi-node project synthesis.

---

## **5. Consistency Checklist**
- [x] **Git Commit**: Metadata/Hardware ignition logic.
- [x] **Tests**: 72 tests passing (100% green).
- [x] **Nomenclature**: Hub, Engine, Strategic Dashboard, Ignite.
