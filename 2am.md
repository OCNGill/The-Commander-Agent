# **The-Commander — Master Plan (v1.2.8)**

**Date:** 2025-12-31 04:30  
**Status:** Phase 5 Finalized | **Strategic Dashboard Active**  
**Authoritative State:** Command & Control Logic defined for Strategic GUI.

---

## **1. Authoritative Architecture & Topology**

### **Cluster Nodes & Hardware Calibration**
| Node ID | Physical Host | Hardware | Bench (t/s) | Model Configuration |
| :--- | :--- | :--- | :--- | :--- |
| **node-main** | Gillsystems-Main | Radeon 7900XTX | **130** | Qwen3-Coder-25B (131k ctx, 999 NGL) |
| **node-htpc** | Gillsystems-HTPC | Radeon 7600 | **60** | Granite-4.0-h-tiny (114k ctx, 40 NGL) |
| **node-steamdeck**| Steam Deck | Custom APU | **30** | Granite-4.0-h-tiny (21k ctx, 32 NGL) |
| **node-laptop**| Gillsystems-Laptop| Integrated | **9** | Granite-4.0-h-tiny (21k ctx, 999 NGL) |

---

## **2. Build Progress (7D Agile)**

### **✅ Phase 5: TUI Dashboard & Engine Ignition**
- Real-time performance monitoring and automated hardware backend (llama.cpp) ignition.

### **🔄 Phase 6: Strategic GUI — "The War Room" (DEVELOP)**
*Objective: Transform the OS into a graphical Command & Control center.*

- [x] **React/Vite Infrastructure**: Modern web dashboard foundation built with tactical design system.
- [x] **Backend Integration**: Connected the GUI to the SystemManager REST API via tactical `CommanderAPI` client.
- [x] **Real-time WebSockets**: Streaming node health and logs to the browser with zero-latency tactical broadcaster.
- [x] **Dynamic Hardware Dials**: Real-time adjustment of Context (`-c`) and NGL (`-ngl`) per node with remote re-ignition.
- [ ] **Strategic Model Selector**: Remote file browser to locate and swap `.gguf` files in the `model_root_path`.
- [ ] **Binary Authority Control**: Graphical selection/renaming of backend binaries (e.g., `go.exe` vs `llama-server.exe`).
- [ ] **Cluster Heartbeat**: Live visualizations of node TPS load and availability.
- [ ] **Intelligence Log**: Web-based stream of the HTPC MessageStore.
- [ ] **One-Click Deployment**: Single "IGNITE ALL" button to spin up the entire cluster from the browser.

---

## **3. Implementation Philosophy (The Commander Rule)**
- **Robot Discipline**: The AI nodes are "robots" that follow the exact dials set by the Commander.
- **Abstract the "Python Bullshit"**: The GUI should feel like a premium military-grade interface, hiding all code/terminal mess.
- **Speed First**: Initial focus on `llama-cpp` bare-metal performance.

---

## **4. Consistency Checklist**
- [x] **Git Commit**: Metadata/Hardware ignition logic.
- [x] **Tests**: 72 tests passing (100% green).
- [x] **Nomenclature**: Hub, Engine, War-Room, Ignite.
