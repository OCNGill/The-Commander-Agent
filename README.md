## **System Requirements (GOLDEN STANDARD)**

*   **OS**: Windows 10/11 (High Performance Mode)
*   **Python**: **v3.10 ONLY** (Strict Requirement for AI Binaries)
    *   *Warning: Python 3.14 is NOT supported and will cause build failures.*
*   **Node.js**: v18+ (LTS Recommended)
*   **GPU**: AMD Radeon 7000 Series (Optional, for Local LLM)

## **Quick Start**

1.  **Clone**: `git clone https://github.com/OCNGill/The-Commander-Agent.git`
2.  **Ignite**: Run `The_Commander.bat`
    *   *Note: The script will enforce Python 3.10 usage.*
3.  **Command**: Access the dashboard at `http://localhost:5173`

---

## **Architectural Topology**
| Node ID | Physical Host | Hardware | Bench (t/s) | Model Configuration |
| :--- | :--- | :--- | :--- | :--- |
| **node-main** | Gillsystems-Main | Radeon 7900XTX | **130** | Qwen3-Coder-25B (131k ctx, 999 NGL) |
| **node-htpc** | Gillsystems-HTPC | Radeon 7600 | **60** | Granite-4.0-h-tiny (114k ctx, 40 NGL) |
| **node-steamdeck**| Steam Deck | Custom APU | **30** | Granite-4.0-h-tiny (21k ctx, 32 NGL) |
| **node-laptop**| Gillsystems-Laptop| Integrated | **9** | Granite-4.0-h-tiny (21k ctx, 999 NGL) |
