# Ignition & Deployment Protocols

## **System Prerequisites (THE GOLDEN STANDARD)**
To prevent binary incompatibility and dependency hell, this system **STRICTLY REQUIRES**:
*   **Python**: v3.10.x (**Release 3.10.11 Recommended**)
    *   *Note: Python 3.14+ is expressly FORBIDDEN due to lack of Rust binaries.*
*   **Node.js**: v18+ LTS
*   **OS**: Windows 10/11 x64

## **The Ignition Sequence**
Starting a distributed cluster is complex. Gillsystems Commander OS simplifies this into a single authoritative "IGNITE ALL" command.

Execution Order:
1.  **Bootstrap**: Load YAML configurations and initialize in-memory managers.
2.  **Local Engine**: Ignite the `llama-cpp` backend on the local node.
3.  **Relay Fabric**: Establish the central message hub (Relay Server) on the HTPC node.
4.  **Cluster Sync**: Register and ping all defined worker nodes.
5.  **Agent Deployment**: Spin up the assigned agent roles across the validated nodes.

## **Hardware Re-Ignition**
When hardware dials (Context, NGL, Model) are adjusted in the Strategic Dashboard, the affected node undergoes a "Tactical Re-Ignition":
1.  **Shutdown**: The existing backend process is safely terminated.
2.  **Config Sync**: The new parameters are persisted to `relay.yaml`.
3.  **Respawn**: A new process is launched with the updated CLI flags.
4.  **Re-Verify**: The system waits for a HEARTBEAT to confirm the engine is READY.

## **Binary Authority Control**
The system supports multiple backend binaries. By setting the `binary` field in the node configuration, the Commander can choose between different versions or specialized builds of the hardware engine for specific tasks.
- **Default**: `go.exe` (Local development)
- **Production**: `llama-server.exe` (Cluster standard)
