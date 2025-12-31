# User Guide: Operating The-Commander

## **1. Prerequisites**
- **Hardware**: Individual nodes with AMD GPUs (Radeon 7000 series optimized).
- **Software**: Python 3.10+, Node.js (for GUI development), `llama-cpp` binaries (e.g., `go.exe` or `llama-server.exe`).
- **Network**: All nodes must be on the same local network with static IPs if possible.

## **2. Installation & Setup**
1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/OCNGill/The-Commander-Agent.git
    cd The-Commander-Agent
    ```
2.  **Environment Setup**:
    ```bash
    python -m venv .venv
    ./.venv/Scripts/activate
    pip install -r requirements.txt
    ```
3.  **GUI Dependencies**:
    ```bash
    cd commander_os/interfaces/gui
    npm install
    ```

## **3. Launching The War Room**
The War Room is the primary interface for cluster operations. To launch the full stack (REST Backend + React HUD):
```powershell
python main.py war-room-web
```
Access the console at: `http://localhost:5173`

## **4. The Ignition Protocol**
1.  **Select Node**: Click on a node card in the left sidebar (e.g., `node-main`).
2.  **Adjust Dials**:
    - Set **Context Size** to fit your task requirements.
    - Adjust **GPU Layers** to maximize VRAM utilization.
    - Toggle **Flash Attention** for optimized kernels.
3.  **Select Model**: Use the **Model Armory** dropdown to browse `.gguf` files detected on the node.
4.  **Engage Ignition**: Click **IGNITE ALL**.
    - Watch the **Deployment HUD** as it synchronizes the local engine and cluster relay.
    - The status will transition from **OFFLINE** to **ARMED & ACTIVE**.

## **5. Real-time Intelligence Monitoring**
- **Heartbeat Stream**: Use the center table to monitor live TPS (Tokens Per Second) output.
- **Intelligence Log**: Use the bottom panel to search through the cluster's memory store.
- **Filtering**: Click the **Filter** icon to isolate traffic by role (e.g., "SENTINEL") or specific agents.

## **6. Troubleshooting**
- **Engine Failure**: If a node fails to ignite, check the **Intelligence Log** for backend CLI errors.
- **Connection Lost**: Ensure the `host` and `port` settings in `config/relay.yaml` match the local IP of the node-hub.
- **Slow Inference**: Check if GPU layers are correctly offloaded. The **Load** metric in the telemetry strip should reflect GPU activity.
