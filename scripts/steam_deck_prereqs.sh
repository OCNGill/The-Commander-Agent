#!/usr/bin/env bash
set -euo pipefail

echo "\n=== Steam Deck / Linux Prereqs Installer (simple) ===\n"

# Detect package manager
if command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
elif command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt"
else
    echo "Unsupported package manager. Please install git, python3.10 (or python3), pip, nodejs, npm and base-devel/build-essential manually." >&2
    exit 1
fi

if [ "$PKG_MANAGER" = "pacman" ]; then
    echo "Using pacman (Arch/SteamOS). Updating DB and installing packages..."
    sudo pacman -Syu --noconfirm
    sudo pacman -S --noconfirm --needed git nodejs npm base-devel python python-pip
    PY_BIN="python3"
else
    echo "Using apt (Debian/Ubuntu). Updating DB and installing packages..."
    sudo apt-get update -y
    sudo apt-get install -y git curl build-essential
    # Try to install python3.10 explicitly, else python3
    if apt-cache show python3.10 >/dev/null 2>&1; then
        sudo apt-get install -y python3.10 python3.10-venv python3.10-dev python3-pip
        PY_BIN="python3.10"
    else
        sudo apt-get install -y python3 python3-venv python3-dev python3-pip
        PY_BIN="python3"
    fi
    sudo apt-get install -y nodejs npm
fi

# Verify Python executable
if command -v python3.10 >/dev/null 2>&1; then
    PY_BIN="python3.10"
elif command -v python3 >/dev/null 2>&1; then
    PY_BIN="python3"
fi

echo "Detected python: $PY_BIN"

# Create a venv and install requirements if a requirements.txt exists
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [ -f "requirements.txt" ]; then
    echo "Creating .venv (if missing) and installing Python requirements..."
    if [ ! -d ".venv" ]; then
        "$PY_BIN" -m venv .venv
    fi
    # Activate and install
    # shellcheck disable=SC1091
    source .venv/bin/activate
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt || echo "pip install returned nonzero; continuing" >&2
    deactivate
else
    echo "No requirements.txt found in repo root. Skipping Python package install." 
fi

# Final info
cat <<EOF

Done. Summary:
- Git, Node.js/npm and Python installed (via $PKG_MANAGER)
- .venv created (if requirements.txt present) and Python deps installed

Next steps (on the Deck):
1) Edit config/relay.yaml to set this node's entry (node_id, host, port, model_root_path)
2) Make launcher executable: chmod +x the_commander.sh
3) Start services: ./the_commander.sh
   - or run headless backend: source .venv/bin/activate; python main.py commander-gui-dashboard

If you want a non-interactive run (CI style), set NO_VENV=1 to skip venv creation (not recommended):
NO_VENV=1 ./scripts/steam_deck_prereqs.sh

EOF

exit 0
