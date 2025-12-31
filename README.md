# The-Commander: AI Agent Operating System (v1.2.4)

**The-Commander** is a distributed orchestrator for managing a cluster of heterogeneous AI agents. It centralizes state, memory, and task lifecycle management while allowing decentralized execution across specific compute nodes.

---

## **Architectural Topology & Performance**

The system is designed for a multi-node worker topology with a central storage and relay authority. Compute is weighted towards the high-performance Main and HTPC nodes.

| Node | Physical Host | Hardware | Bench (t/s) | Model Root Path |
|------|---------------|----------|-------------|-----------------|
| **Main** | Gillsystems-Main | Radeon 7900XTX | **130** | `C:\Models\Working_Models\` |
| **HTPC** | Gillsystems-HTPC | Radeon 7600 | **60** | `/home/gillsystems-htpc/Desktop/Models/` |
| **SteamDeck** | Steam Deck | Custom APU | **30** | `/home/deck/Desktop/Models/` |
| **Laptop** | Gillsystems-Laptop | Integrated | **9** | `C:\Users\Gillsystems Laptop\Desktop\Models\` |

### **Authoritative Storage (ZFS)**
The **Gillsystems-HTPC** node hosts the primary dataset used by the system:
- **Mountpoint:** `/gillsystems_zfs_pool/AI_storage`
- **Installation Root:** `/home/gillsystems-htpc/`
- **Central Memory:** `commander_memory.db` (SQLite + GZIP)

---

## **The Commander Protocol Layer**

Communication within the cluster is governed by the **Commander Protocol**, a strict message/task envelope system that prevents architectural drift.

- **Standard Envelopes:** All traffic uses `MessageEnvelope` (UUID, Timestamp, Sender/Recipient, Task ID, Priority, GZIP Payload).
- **Intelligent Routing:** Node selection is weighted by TPS benchmarks to maximize throughput.
- **Relay Hub:** Centralized message processing and persistence on the HTPC node.

---

## **Quick Start (War Room)**

1. **Start the Hub (HTPC):**
   ```bash
   python main.py hub --port 8001
   ```
2. **Start the Engine (Any Node):**
   ```bash
   python main.py engine --node node-main
   ```
3. **Launch the Dashboard:**
   ```bash
   python main.py war-room
   ```

---

*Property of Gillsystems. 7D Agile methodology enforced. Alignment is Absolute.*
