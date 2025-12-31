# **The-Commander: Distributed AI Orchestration System**

**Version:** 1.2.19  
**Status:** GUI Complete - Model Selection Working - Chat In Progress  
**Next Release:** 1.3.0 (Multi-Node Chat Integration)

---

## **System Requirements**

*   **OS**: Windows 10/11 or Linux (Ubuntu 20.04+)
*   **Python**: **v3.10 ONLY** (Strict Requirement)
    *   *Warning: Python 3.14+ will cause dependency failures*
*   **Node.js**: v18+ (LTS Recommended)
*   **GPU**: AMD Radeon 7000 Series (Optional, for Local LLM Acceleration)

## **Quick Start (Single Node)**

1.  **Clone Repository**:
    ```bash
    git clone https://github.com/OCNGill/The-Commander-Agent.git
    cd The-Commander-Agent
    ```

2.  **Install Dependencies**:
    ```bash
    # Windows
    py -3.10 -m pip install -r requirements.txt
    
    # Linux
    python3.10 -m pip install -r requirements.txt
    ```

3.  **Launch System**:
    ```bash
    # Windows
    The_Commander.bat
    
    # Linux
    ./the_commander.sh
    ```

4.  **Access Dashboard**: Open browser to `http://localhost:5173`

---

## **Multi-Node Deployment (Full Functionality)**

For complete model discovery and distributed orchestration across all nodes:

1.  **Clone Repository on Each Node**:
    ```bash
    # On each physical machine (Main, HTPC, Steam-Deck, Laptop)
    git clone https://github.com/OCNGill/The-Commander-Agent.git
    cd The-Commander-Agent
    ```

2.  **Install Dependencies on Each Node**:
    ```bash
    # Run on each node
    py -3.10 -m pip install -r requirements.txt  # Windows
    python3.10 -m pip install -r requirements.txt  # Linux
    ```

3.  **Verify Node Configuration**:
    - Check `config/relay.yaml` for correct IP addresses and ports
    - Ensure `model_root_path` points to each node's model directory

4.  **Launch on Each Node**:
    ```bash
    # Each node automatically detects its identity based on port
    The_Commander.bat  # Windows
    ./the_commander.sh  # Linux
    ```

5.  **Verify Network Connectivity**:
    - Each node's API should be accessible at `http://<node-ip>:<port>`
    - Test from any node: `curl http://10.0.0.164:8000/nodes`

**Why Multi-Node Deployment?**
- **Model Discovery**: Each node scans its own filesystem and reports available models
- **Distributed Inference**: Chat requests route to highest-ranking available node
- **Load Balancing**: System automatically distributes work across active nodes
- **Fault Tolerance**: If one node fails, others continue operating

---

## **Architectural Topology**
| Node ID | Physical Host | Hardware | Bench (t/s) | Model Configuration |
| :--- | :--- | :--- | :--- | :--- |
| **Gillsystems-Main** | Gillsystems-Main | Radeon 7900XTX | **130** | Qwen3-Coder-25B (131k ctx, 999 NGL) |
| **Gillsystems-HTPC** | Gillsystems-HTPC | Radeon 7600 | **60** | Granite-4.0-h-tiny (114k ctx, 40 NGL) |
| **Gillsystems-Steam-Deck**| Gillsystems-Steam-Deck | Custom APU | **30** | Granite-4.0-h-tiny (21k ctx, 32 NGL) |
| **Gillsystems-Laptop**| Gillsystems-Laptop| Integrated | **9** | Granite-4.0-h-tiny (21k ctx, 999 NGL) |
