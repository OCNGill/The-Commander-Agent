# User Guide & Troubleshooting

## **Prerequisites (The Golden Standard)**
The **Gillsystems Commander OS** system requires a specific environment to function correctly, particularly to support the advanced AI binaries.

*   **Operating System**: Windows 10 or 11 (64-bit).
*   **Python**: **Version 3.10.x is MANDATORY**.
    *   The system includes an auto-provisioner, but if that fails, you must install it manually.
    *   **Download**: [Python 3.10.11 Installer](https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe)
    *   **Important**: During manual installation, verify the install path or ensure "Add Python to PATH" is checked.
*   **Node.js**: Version 18+ (LTS).

---

## **Troubleshooting Ignition**

### **Issue: "Auto-provisioning failed" or Python not found**
If the automated script fails to install Python 3.10 automatically (often due to permissions or complex usernames with spaces):

1.  **Manual Install**:
    *   Download the installer from the link above.
    *   Run it. Select **"Install Now"** (not custom) or ensure you know the path.
    *   **Critical**: Check the box **"Add Python 3.10 to PATH"** at the bottom of the first screen.

2.  **Manual Override**:
    *   If you have Python installed in a non-standard location, you can edit `The_Commander.bat`.
    *   Find the line: `set "TARGET_PYTHON=py -3.10"`
    *   Change it to your path: `set "TARGET_PYTHON="C:\Path\To\Your\python.exe""`

### **Issue: "Hub is unreachable"**
*   **Check Port 8000**: Ensure no other service is using port 8000.
*   **Firewall**: Allow `python.exe` through the Windows Firewall if prompted.
*   **Logs**: Check the `COMMANDER_BACKEND` console window for specific error messages.

---

## **The "7D" Workflow**
1.  **Discovery**: Review `PRODUCT_DESCRIPTION_MVP1.0.md` to understand goals.
2.  **Design**: Check `system_architecture_v1.2.0.mmd` for topology.
3.  **Development**: Code in `commander_os/`.
4.  **Deployment**: Use `The_Commander.bat` to ignite.
5.  **Documentation**: Keep this guide updated.
