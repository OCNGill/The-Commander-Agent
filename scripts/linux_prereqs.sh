#!/usr/bin/env bash
set -euo pipefail

echo ""
echo "============================================================"
echo "  🛡️  GILLSYSTEMS COMMANDER OS - Linux Prerequisites"
echo "  Installing ALL dependencies for the_commander.sh"
echo "============================================================"
echo ""

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

# Required versions
REQUIRED_NODE_MAJOR=20
REQUIRED_PYTHON="3.10"

# Detect package manager
if command -v pacman >/dev/null 2>&1; then
    PKG_MANAGER="pacman"
elif command -v apt-get >/dev/null 2>&1; then
    PKG_MANAGER="apt"
else
    echo "❌ ERROR: Unsupported package manager. Requires pacman or apt." >&2
    exit 1
fi

echo "[1/5] 🔧 Installing system build dependencies..."
if [ "$PKG_MANAGER" = "pacman" ]; then
    echo "  → Using pacman (Arch/SteamOS)"
    sudo pacman -Syu --noconfirm
    sudo pacman -S --noconfirm --needed git curl wget base-devel python python-pip
else
    echo "  → Using apt (Debian/Ubuntu)"
    sudo apt-get update -y
    sudo apt-get install -y git curl wget build-essential libssl-dev zlib1g-dev \
        libbz2-dev libreadline-dev libsqlite3-dev libncursesw5-dev \
        xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
fi

echo ""
echo "[2/5] 🐍 Ensuring Python ${REQUIRED_PYTHON} is available..."

# Check if python3.10 exists and is usable
PY_BIN=""
if command -v python3.10 >/dev/null 2>&1 && python3.10 --version >/dev/null 2>&1; then
    PY_BIN="python3.10"
    echo "  ✓ Found python3.10: $(python3.10 --version)"
else
    echo "  ⚠️  python3.10 not found. Installing via pyenv..."
    
    # Install pyenv if not present
    if [ ! -d "$HOME/.pyenv" ]; then
        echo "  → Installing pyenv..."
        curl https://pyenv.run | bash
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init --path)"
        eval "$(pyenv init -)"
    else
        export PYENV_ROOT="$HOME/.pyenv"
        export PATH="$PYENV_ROOT/bin:$PATH"
        eval "$(pyenv init --path)" || true
        eval "$(pyenv init -)" || true
    fi
    
    # Install Python 3.10.13 if not present
    if ! pyenv versions | grep -q "3.10.13"; then
        echo "  → Building Python 3.10.13 (this may take a few minutes)..."
        pyenv install 3.10.13
    fi
    
    PY_BIN="$HOME/.pyenv/versions/3.10.13/bin/python3.10"
    
    if [ ! -f "$PY_BIN" ]; then
        echo "❌ ERROR: Failed to install Python 3.10.13" >&2
        exit 1
    fi
    
    echo "  ✓ Python 3.10.13 installed via pyenv"
fi

echo ""
echo "[3/5] 📦 Ensuring Node.js ${REQUIRED_NODE_MAJOR}+ and npm are available..."

NODE_OK=false
if command -v node >/dev/null 2>&1; then
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -ge "$REQUIRED_NODE_MAJOR" ]; then
        echo "  ✓ Found Node.js v$(node -v) (npm v$(npm -v))"
        NODE_OK=true
    else
        echo "  ⚠️  Node.js v$NODE_VERSION found but v${REQUIRED_NODE_MAJOR}+ required"
    fi
fi

if [ "$NODE_OK" = false ]; then
    echo "  → Installing Node.js ${REQUIRED_NODE_MAJOR} LTS..."
    
    # Remove old versions if present
    if [ "$PKG_MANAGER" = "apt" ]; then
        sudo apt-get remove -y nodejs npm 2>/dev/null || true
        sudo apt-get purge -y nodejs npm 2>/dev/null || true
        sudo apt-get autoremove -y || true
    fi
    
    # Install Node 20 via official binary
    NODEVER="20.19.1"
    NODETAR="node-v${NODEVER}-linux-x64.tar.xz"
    
    if [ ! -f "/usr/local/bin/node" ] || [ "$(/usr/local/bin/node -v 2>/dev/null | cut -d'v' -f2 | cut -d'.' -f1)" != "20" ]; then
        echo "  → Downloading Node.js v${NODEVER}..."
        wget -q --show-progress "https://nodejs.org/dist/v${NODEVER}/${NODETAR}"
        echo "  → Extracting to /usr/local..."
        sudo tar -C /usr/local --strip-components=1 -xJf "$NODETAR"
        rm "$NODETAR"
        sudo chmod -R a+rX /usr/local/bin /usr/local/lib 2>/dev/null || true
    fi
    
    # Verify installation
    if ! /usr/local/bin/node -v >/dev/null 2>&1; then
        echo "❌ ERROR: Node.js installation failed" >&2
        exit 1
    fi
    
    echo "  ✓ Node.js v$(/usr/local/bin/node -v) installed (npm v$(/usr/local/bin/npm -v))"
fi

# Ensure node/npm are in PATH (prefer /usr/local/bin)
export PATH="/usr/local/bin:$PATH"

echo ""
echo "[4/5] 🐍 Creating Python virtual environment and installing dependencies..."

if [ ! -d ".venv" ]; then
    echo "  → Creating .venv with $PY_BIN..."
    "$PY_BIN" -m venv .venv
fi

echo "  → Activating venv and upgrading pip..."
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip --quiet

if [ -f "requirements.txt" ]; then
    echo "  → Installing Python packages from requirements.txt..."
    python -m pip install -r requirements.txt
else
    echo "  ⚠️  No requirements.txt found - skipping Python package install"
fi

deactivate

echo ""
echo "[5/5] ✅ Validating installation..."

# Final validation
ERRORS=0

if ! command -v python3 >/dev/null 2>&1; then
    echo "  ❌ python3 command not found"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ python3: $(python3 --version)"
fi

if ! command -v node >/dev/null 2>&1; then
    echo "  ❌ node command not found"
    ERRORS=$((ERRORS + 1))
else
    NODE_VER=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VER" -ge "$REQUIRED_NODE_MAJOR" ]; then
        echo "  ✓ node: v$(node -v)"
    else
        echo "  ❌ node v$NODE_VER < v${REQUIRED_NODE_MAJOR} required"
        ERRORS=$((ERRORS + 1))
    fi
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "  ❌ npm command not found"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ npm: v$(npm -v)"
fi

if [ ! -d ".venv" ]; then
    echo "  ❌ .venv not created"
    ERRORS=$((ERRORS + 1))
else
    echo "  ✓ .venv created"
fi

echo ""
if [ $ERRORS -eq 0 ]; then
    echo "============================================================"
    echo "  ✅ ALL PREREQUISITES INSTALLED SUCCESSFULLY"
    echo "============================================================"
    echo ""
    echo "Next steps:"
    echo "  1. Review config/relay.yaml for cluster topology"
    echo "  2. Make launcher executable: chmod +x the_commander.sh"
    echo "  3. Launch cluster: ./the_commander.sh"
    echo ""
    echo "For headless backend only:"
    echo "  source .venv/bin/activate"
    echo "  python main.py commander-gui-dashboard --host 0.0.0.0 --port 8001"
    echo ""
    exit 0
else
    echo "============================================================"
    echo "  ❌ INSTALLATION INCOMPLETE - $ERRORS errors found"
    echo "============================================================"
    exit 1
fi
