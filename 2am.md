# **The-Commander — Master Plan (v1.2.5)**

**Date:** 2025-12-31 04:00  
**Status:** Phase 5 Finalized | **Strategic Dashboard & Engine Ignition Active**  
**Authoritative State:** Hardware-Optimized Engine Management Aligned to ZFS Memory Store.

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

### **✅ Phase 5: TUI Dashboard & Engine Ignition (DEVELOP)**
- [x] **Strategic Dashboard**: Real-time TUI visualization with live cluster traffic log.
- [x] **Engine Ignition**: One-click automation to launch `llama.cpp` backends with hardware-optimized flags (`-ngl`, `-fa`, `-c`).
- [x] **CLI Entry**: `main.py` with `hub`, `engine`, and `war-room` commands fully functional.
- [x] **ZFS Persistence**: Every message in the traffic log is committed to the HTPC ZFS store.

### **🔄 Phase 6: Strategic GUI (Next Focus)**
- [ ] **React/Vite Infrastructure**: Modern web dashboard for the Commander's War Room.
- [ ] **Real-time WebSockets**: Streaming node health and logs to the browser.
- [ ] **Memory Browser**: Interactive navigation of the `MessageStore` message history.
- [ ] **Config Overlord**: UI-based controls for role permissions and node settings.

---

## **3. Implementation Rules (The Commander Rule)**
- **Binary Authority**: Use `go.exe` (Win) or `./go` (Linux) as specified per node.
- **Hardware First**: Ensure `-ngl` and `-fa` are always pushed to the limit of the specific GPU.
- **One-Click Only**: All complex subprocess management must be hidden from the user.

---

## **4. Consistency Checklist**
- [x] **Git Commit**: Hardware engine ignition and log streaming logic.
- [x] **Tests**: 72 tests passing (100% green).
- [x] **Nomenclature**: Aligned to Hub/Engine/War-Room strategic terms.
