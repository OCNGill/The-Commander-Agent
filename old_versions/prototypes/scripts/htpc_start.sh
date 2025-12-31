#!/usr/bin/env bash
# Starter launcher for HTPC relay + agent. Place this at /home/stephen/scripts/htpc_start.sh
# Make executable: chmod +x htpc_start.sh

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RELAY_PY="$BASE_DIR/relay/relay_server.py"
AGENT_PY="$BASE_DIR/agents/htpc_agent.py"
LOG_DIR="$BASE_DIR/logs"

mkdir -p "$LOG_DIR/relay" "$LOG_DIR/agents" "$LOG_DIR/artifacts"

# Start relay in background
nohup python3 "$RELAY_PY" > "$LOG_DIR/relay/relay.out" 2>&1 &
RELAY_PID=$!

echo "Started relay (PID=$RELAY_PID)"

# Give relay a moment
sleep 1

# Start agent in background
nohup python3 "$AGENT_PY" > "$LOG_DIR/agents/agent.out" 2>&1 &
AGENT_PID=$!

echo "Started agent (PID=$AGENT_PID)"

# Optionally wait or print PIDs and exit
exit 0
