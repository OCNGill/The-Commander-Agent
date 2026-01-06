# **The-Commander: Distributed AI Orchestration System**

**Version:** 1.2.21  
**Status:** Unified Cluster Memory Convergence & Agent Foundations  
**Next Release:** 1.5.0 (Autonomous Intelligence Era)

---

## **System Requirements**

*   **OS**: Windows 10/11 or Linux (Ubuntu 20.04+)
*   **Python**: **v3.10 ONLY** (Strict Requirement)
    *   *Warning: Python 3.14+ will cause dependency failures*
*   **Node.js**: v20+ (LTS Required for Vite compatibility)
*   **GPU**: AMD Radeon 7000 Series (Optional, for Local LLM Acceleration)

---

## **Automated Setup (Recommended for Linux)**

For automated installation of all dependencies (Python 3.10, Node.js 20+, npm, build tools):

```bash
cd The-Commander-Agent
./scripts/linux_prereqs.sh
```

This script will:
- Install Node.js 20+ (required for Vite frontend)
- Ensure Python 3.10 is available (via pyenv if needed)
- Create virtual environment and install Python dependencies
- Validate all prerequisites before completion

---

## **Quick Start (Single Node)**

1.  **Clone Repository**:
    ```bash
    git clone https://github.com/OCNGill/The-Commander-Agent.git
    cd The-Commander-Agent
    ```

2.  **Install Dependencies (run the platform pre-req first)**:
    ```bash
    # Linux (recommended)
    ./scripts/linux_prereqs.sh

    # Windows (run as Administrator)
    # From Explorer: Right-click `install_prereqs.bat` and choose "Run as administrator"
    # Or in an elevated PowerShell prompt:
    .\install_prereqs.bat
    ```

    After the prereq installer finishes, continue with the launcher step below to start the Commander OS.

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
    # Automated (Linux) - Recommended
    ./scripts/linux_prereqs.sh
    
    # Manual Windows
    py -3.10 -m pip install -r requirements.txt
    
    # Manual Linux
    python3.10 -m pip install -r requirements.txt
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

---

## **Changelog**

### Version 1.3
- Implemented the new storage framework for Commander OS.
- Added agent-specific storage modules for Commander and Recruiter agents.
- Updated documentation to reflect the new storage architecture.

---

## **Documentation Links**

- [Storage System Implementation](docs/STORAGE_IMPLEMENTATION_COMPLETE.md)
- [Storage Architecture](docs/STORAGE_ARCHITECTURE.md)
- [Commander OS Agent Storage Info](docs/Commander_OS_agent_storage_info.md)
