# The War Room: Strategic Command & Control

The War Room is the high-fidelity graphical interface for The-Commander OS. It is built with **React, Vite, and Framer Motion** to provide a premium, tactical experience.

## **Tactical Features**

### **1. Real-time Heartbeat Stream**
The interface maintains a persistent WebSocket link to the Hub. Every system state change (node status, agent activity, performance spikes) is broadcast and rendered instantly.
- **Node Cards**: Visual indicators of node health and live TPS gauges.
- **Telemetry Strip**: Detailed performance metrics including Load, Uptime, and inference speed.

### **2. Dynamic Hardware Dials**
Unlike static configurations, the War Room allows for "hot-dialing" hardware parameters:
- **Context Size (`-c`)**: Adjust the memory window of the LLM.
- **GPU Layers (`-ngl`)**: Offload specifically calculated layers to VRAM.
- **Flash Attention (FA)**: Toggle high-performance attention kernels.

### **3. Strategic Model Selector**
Nodes scan their local `model_root_path` for `.gguf` weights. The GUI provides a remote file browser to swap models across the cluster without touching a terminal.

### **4. Binary Authority**
The Commander can specify the exact backend binary for each node (e.g., swapping a stable `llama-server.exe` for a developmental `go.exe`).

### **5. Intelligence Log**
A searchable, filterable stream of the cluster's collective memory.
- **Search**: Instant grep-like search across the MessageStore.
- **Filters**: Isolate traffic by Agent Role (Sentinel, Scout, Orchestrator) or specific Node.

### **6. Deployment HUD**
During the "Ignite All" sequence, a military-grade overlay engages, showing the progress of system-wide initialization protocols.

## **Tech Stack**
- **Frontend**: React 18, Vite.
- **Styling**: Vanilla CSS (Tactical Design System).
- **Communication**: REST API + WebSockets.
- **Icons**: Lucide-React.
- **Animations**: Framer Motion.
