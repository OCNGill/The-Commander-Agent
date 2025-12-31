# The-Commander: AI Agent Operating System (v1.2.15)

**The-Commander** is a distributed military-grade orchestrator for managing a cluster of heterogeneous AI agents. It centralizes state, memory, and task lifecycle management while allowing decentralized execution across specific compute nodes via "The War Room" GUI.

---

## **Strategic Control: The War Room**
The system now features a high-fidelity React-based Command & Control center:
- **Real-time Heartbeat**: Zero-latency visualization of cluster TPS load and node availability.
- **Dynamic Hardware Dials**: Hot-swap Context (`-c`) and NGL (`-ngl`) parameters for local or remote engines.
- **Binary Authority**: Explicit control over backend binaries (e.g., `go.exe` vs `llama-server.exe`).
- **One-Click Ignite**: Synchronized cluster-wide deployment with a high-fidelity progression HUD.
- **Intelligence Stream**: Global search and multi-layer filtering of the HTPC MessageStore.

---

## **Architectural Topology**
| Node ID | Physical Host | Hardware | Bench (t/s) | Model Configuration |
| :--- | :--- | :--- | :--- | :--- |
| **node-main** | Gillsystems-Main | Radeon 7900XTX | **130** | Qwen3-Coder-25B (131k ctx, 999 NGL) |
| **node-htpc** | Gillsystems-HTPC | Radeon 7600 | **60** | Granite-4.0-h-tiny (114k ctx, 40 NGL) |
| **node-steamdeck**| Steam Deck | Custom APU | **30** | Granite-4.0-h-tiny (21k ctx, 32 NGL) |
| **node-laptop**| Gillsystems-Laptop| Integrated | **9** | Granite-4.0-h-tiny (21k ctx, 999 NGL) |

### **Authoritative Storage (ZFS/MessageStore)**
- **Central Memory:** `commander_memory.db` (SQLite + SQLAlechemy + GZIP)
- **Persistence Layer:** Gillsystems-HTPC ZFS pool for long-term intelligence storage.

---

## **Operation Protocols**

1. **Ignite the Fabric:**
   ```powershell
   python main.py war-room-web
   ```
2. **Access the Console:** Open browser to `http://localhost:5173`.
3. **Command Deployment:** Select a node, adjust dials, specify model, and hit **IGNITE ALL**.

---

*Property of Gillsystems. 7D Agile methodology enforced. Alignment is Absolute.*
