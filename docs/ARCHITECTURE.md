# System Architecture: Gillsystems Commander OS

## **Core Philosophy**
Gillsystems Commander OS is built as an **Agentic Operating System**. It moves away from monolithic AI applications towards a distributed, modular, and authoritative orchestration layer.

## **Component Breakdown**

### **1. The Hub (REST API & WebSockets)**
*   **Entry Point**: `commander_os/interfaces/rest_api.py`
*   **Role**: The central command authority. It exposes a RESTful interface for configuration and control, and a WebSocket broadcaster for real-time tactical updates.
*   **Broadcasting**: Uses `ConnectionManager` to push system snapshots to all connected GUI clients with minimal latency.

### **2. System Manager (The Orchestrator)**
*   **Entry Point**: `commander_os/core/system_manager.py`
*   **Role**: The brain of the individual node. It manages the lifecycle of the Relay, Hardware Engines, and Agents.
*   **Ignition**: Handles the `_ignite_hardware_engine` process, translating high-level dials (Context, NGL, FA) into bare-metal CLI commands for the `llama-cpp` backend.

### **3. State Manager (Ground Truth)**
*   **Entry Point**: `commander_os/core/state.py`
*   **Role**: Thread-safe, in-memory store for the current health and performance of every node and agent in the cluster.
*   **Metrics**: Tracks live TPS (Tokens Per Second), Load, and Uptime.

### **4. MessageStore (Persistence)**
*   **Entry Point**: `commander_os/core/memory.py`
*   **Role**: Persistent storage using SQLite and SQLAlchemy.
*   **GZIP Compression**: All message contents are compressed before storage to manage long-term intelligence growth on the ZFS pool.

### **5. Node & Agent Managers**
*   **Role**: Registry and logical management. NodeManager handles performance-weighted load balancing, while AgentManager manages role-based agent deployment.

## **Data Flow**
1.  **Command**: User adjusts a dial in the Strategic Dashboard.
2.  **Request**: GUI sends POST to `/nodes/{id}/engine`.
3.  **Persist**: ConfigManager updates `relay.yaml`.
4.  **Action**: SystemManager shuts down existing engine and re-ignites with new binary/flags.
5.  **Feedback**: StateManager updates status to `STARTING`, then `READY`. WebSocket pushes update to GUI.
