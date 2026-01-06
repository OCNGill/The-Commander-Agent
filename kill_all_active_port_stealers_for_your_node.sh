#!/usr/bin/env bash

# GILLSYSTEMS COMMANDER OS // TACTICAL PORT CLEARANCE
# This script kills any processes holding onto the Commander ports to prevent "Address already in use" errors.

echo "═══════════════════════════════════════════════════════════════════"
echo "  🛡️  GILLSYSTEMS COMMANDER OS - Tactical Port Clearance"
echo "═══════════════════════════════════════════════════════════════════"

PORTS=(8000 8001 8002 8003 5173 5174 5175)

echo "[1/2] Terminating processes on critical ports..."
for port in "${PORTS[@]}"; do
    if command -v fuser >/dev/null 2>&1; then
        if fuser -k "$port/tcp" >/dev/null 2>&1; then
            echo "  ✓ Cleared Port: $port"
        fi
    else
        # Fallback if fuser is missing
        pid=$(ss -tulpn 2>/dev/null | grep ":$port" | awk '{print $7}' | cut -d',' -f2 | cut -d'=' -f2)
        if [ -z "$pid" ]; then
            pid=$(lsof -t -i:"$port" 2>/dev/null)
        fi
        
        if [ -n "$pid" ]; then
            kill -9 "$pid"
            echo "  ✓ Force Killed PID $pid on Port $port"
        fi
    fi
done

echo "[2/2] Cleaning up ghost processes by name..."
pkill -f "python main.py" >/dev/null 2>&1 && echo "  ✓ Terminated Python backend"
pkill -f "vite" >/dev/null 2>&1 && echo "  ✓ Terminated Vite frontend"

echo "═══════════════════════════════════════════════════════════════════"
echo "  ✅ SYSTEM CLEARANCE COMPLETE"
echo "═══════════════════════════════════════════════════════════════════"
