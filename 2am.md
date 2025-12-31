# **The-Commander — Master Plan (v1.2.4)**

**Date:** 2025-12-31 03:10  
**Status:** Protocol Integration & Path Calibration Complete | **Authoritative State**  

---

## **1. Authoritative Architecture & Topology**

### **Cluster Nodes & Hardware Mapping**
| Node ID | Physical Host | Hardware | Bench (t/s) | Model Root Path |
| :--- | :--- | :--- | :--- | :--- |
| **node-main** | Gillsystems-Main | Radeon 7900XTX | **130** | `C:\Models\Working_Models\` |
| **node-htpc** | Gillsystems-HTPC | Radeon 7600 | **60** | `/home/gillsystems-htpc/Desktop/Models/` |
| **node-steamdeck**| Steam Deck | Custom APU | **30** | `/home/deck/Desktop/Models/` |
| **node-laptop**| Gillsystems-Laptop| Integrated | **9** | `C:\Users\Gillsystems Laptop\Desktop\Models\` |

### **HTPC Storage (ZFS Pool)**
- **Authoritative Mount**: `/gillsystems_zfs_pool/AI_storage/`
- **Memory Master**: `commander_memory.db` (Hosted on HTPC).

---

## **2. Build Progress (7D Agile)**

### **✅ Core Infrastructure (Phase 1-4)**
- **ConfigManager**: Fully aware of node performance and local model paths.
- **NodeManager**: Intelligent load balancing based on 130/60/30/9 benchmarks.
- **Relay Hub**: Central transmission server active on node-htpc:8001.
- **Memory Store**: Persistent GZIP-compressed message history on ZFS.

### **🔄 Dashboard & War Room (Phase 5 - Current)**
- [x] **TUI Dashboard**: Real-time visualization of node health and benchmarks.
- [x] **CLI Entry**: `main.py` with `hub`, `engine`, and `war-room` commands.
- [ ] **Log Stream**: Tailing the `MessageStore` messages into the TUI.

---

## **3. TO-DO: Machine-Specific Implementation (The Friggin' Commander Rule)**
- [ ] **Model Ingestion**: Map specific .gguf or vLLM container names to the `model_root_path`.
- [ ] **One-Click Deployment**: Finalize `.bat` and `.sh` files *only after* model mapping is foolproof.
- [ ] **ZFS Sync Logic**: Ensure artifacts and checkpoints are committed back to the HTPC pool.

---

## **4. Consistency Checklist**
- [x] **Git Commit**: Calibration of model root paths.
- [x] **Tests**: 72 tests passing (100% green).
- [x] **Topology**: Aligned to IPs 164 (Main), 42 (HTPC), 139 (SD), 93 (Laptop).
