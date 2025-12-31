# **The-Commander — Master Plan (v1.2.3)**

**Date:** 2025-12-31 03:00  
**Status:** Phase 5 Infrastructure Active | **TUI Dashboard Operational**  
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

---

## **3. Build Status (7D Agile)**

### **✅ Phase 1-3: Core Operating System**
- Framework, Memory, and REST API operational.

### **✅ Phase 4: Protocol Integration**
- `MessageEnvelope` enforced, Relay Hub/Client implemented, benchmark-aware routing.

### **🔄 Phase 5: TUI Dashboard (Current Focus)**
- [x] **Framework Setup**: `Rich` library integrated for terminal UI.
- [x] **Real-time Monitoring**: Visualizing node heartbeats and active TPS benchmarks.
- [x] **Agent View**: Tracking role and node assignment for all active processes.
- [x] **CLI Entry Point**: `main.py` created with `relay`, `start`, and `dashboard` commands.
- [ ] **Log Stream**: Tailing the `MessageStore` in the terminal dashboard.

---

## **4. The Road to MVP (Next Steps)**

### **Phase 6: Web GUI (DEVELOP)**
- React/Vite dashboard for configuration and memory browsing.

---

## **5. Consistency Checklist**
- [x] **README.md** Sync complete.
- [x] **Git Commit**: Phase 5 Layout closure.
- [x] **Tests**: 72 tests passing (100% coverage).
- [x] **Entry Point**: `python main.py dashboard` verified.
