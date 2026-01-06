#!/bin/bash

# GILLSYSTEMS COMMANDER OS // CLUSTER IGNITION (Linux/Unix)

echo -e "\n \e[1;34m############################################################\e[0m"
echo -e " \e[1;34m##                                                        ##\e[0m"  
echo -e " \e[1;34m##        🛡️  GILLSYSTEMS COMMANDER OS v1.2.20           ##\e[0m"  
echo -e " \e[1;34m##            STRATEGIC CLUSTER ORCHESTRATION             ##\e[0m"  
echo -e " \e[1;34m##                                                        ##\e[0m"
echo -e " \e[1;34m############################################################\e[0m\n"# 1. System Check
echo "[1/4] EXAMINING OPERATIONAL ENVIRONMENT..."
if ! command -v python3 &> /dev/null; then
    echo -e "\e[1;31m[ERROR] python3 not found.\e[0m"
    exit 1
fi
if ! command -v npm &> /dev/null; then
    echo -e "\e[1;31m[ERROR] npm not found.\e[0m"
    exit 1
fi
echo "[STATUS] Core binaries validated."

# 2. Python Environment
echo -e "\n[2/4] SYNCHRONIZING ORCHESTRATION LAYER..."
if [ ! -d ".venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv .venv
fi
echo "[INFO] Activating virtual environment..."
source .venv/bin/activate

echo "[INFO] Installing/Updating Python dependencies..."
echo "[COMMAND] pip install -r requirements.txt"
# Removed --quiet to show progress
pip install --upgrade pip
pip install -r requirements.txt

# 3. GUI Environment
echo -e "\n[3/4] SYNCHRONIZING STRATEGIC DASHBOARD..."
cd commander_os/interfaces/gui || exit
if [ ! -d "node_modules" ]; then
    echo "[INFO] Node modules missing. Initiating full tactical download..."
    echo "[COMMAND] npm install"
    npm install
else
    echo "[INFO] node_modules detected. Verifying integrity..."
    echo "[COMMAND] npm install --prefer-offline"
    npm install --prefer-offline
fi
cd ../../../

# 4. Ignite
echo -e "\n[4/4] ENGAGING ALL PROTOCOLS..."

# Determine background execution
source .venv/bin/activate
# Keep stdout/stderr visible for the commander until the background task is fully confirmed
python main.py commander-gui-dashboard &
BACKEND_PID=$!
echo -e "\e[1;33m[!] Orchestration Backend Ignited (PID: $BACKEND_PID)\e[0m"

cd commander_os/interfaces/gui || exit
npm run dev &
FRONTEND_PID=$!
echo -e "\e[1;33m[!] Strategic Dashboard Ignited (PID: $FRONTEND_PID)\e[0m"

echo -e "\n \e[1;32m############################################################\e[0m"
echo -e " \e[1;32m##                                                        ##\e[0m"
echo -e " \e[1;32m##            ✅ CLUSTER IGNITION SUCCESSFUL             ##\e[0m"
echo -e " \e[1;32m##                                                        ##\e[0m"
echo -e " \e[1;32m##  🌐 ACCESS STRATEGIC DASHBOARD: http://localhost:5173  ##\e[0m"
echo -e " \e[1;32m##                                                        ##\e[0m"
echo -e " \e[1;32m############################################################\e[0m\n"

echo "[INFO] Press Ctrl+C to shutdown all cluster protocols."

# Cleanup on exit
trap "echo -e '\n[!] SHUTTING DOWN PORTS...'; kill $BACKEND_PID $FRONTEND_PID; exit" INT TERM
wait
