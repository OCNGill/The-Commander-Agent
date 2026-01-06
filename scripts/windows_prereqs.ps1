#Requires -RunAsAdministrator

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  GILLSYSTEMS COMMANDER OS - Windows Prerequisites" -ForegroundColor Cyan
Write-Host "  Installing ALL dependencies for The_Commander.bat" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Stop"
$REPO_ROOT = Split-Path -Parent $PSScriptRoot
Set-Location $REPO_ROOT

# Required versions
$REQUIRED_NODE_MAJOR = 20
$REQUIRED_PYTHON = "3.10"

# Detect package manager
$PKG_MANAGER = $null
if (Get-Command winget -ErrorAction SilentlyContinue) {
    $PKG_MANAGER = "winget"
    Write-Host "  [OK] Detected winget" -ForegroundColor Green
} elseif (Get-Command choco -ErrorAction SilentlyContinue) {
    $PKG_MANAGER = "choco"
    Write-Host "  [OK] Detected Chocolatey" -ForegroundColor Green
} else {
    Write-Host "[ERROR] No package manager found. Please install winget or Chocolatey:" -ForegroundColor Red
    Write-Host "  winget: Built into Windows 11 and Windows 10 (via App Installer)" -ForegroundColor Yellow
    Write-Host "  choco: https://chocolatey.org/install" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "[1/5] Installing system dependencies (Git)..." -ForegroundColor Cyan

# Check and install Git
if (!(Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host "  -> Installing Git..."
    if ($PKG_MANAGER -eq "winget") {
        winget install --id Git.Git --accept-package-agreements --accept-source-agreements --silent
    } else {
        choco install git -y
    }
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
} else {
    Write-Host "  [OK] Git already installed: $(git --version)" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/5] Ensuring Python $REQUIRED_PYTHON is available..." -ForegroundColor Cyan

$PY_BIN = $null
$PY_FOUND = $false

# Try to find Python 3.10
$pythonCommands = @("python3.10", "python", "py")
foreach ($cmd in $pythonCommands) {
    try {
        $version = & $cmd --version 2>&1 | Out-String
        if ($version -match "Python 3\.10") {
            $PY_BIN = $cmd
            $PY_FOUND = $true
            Write-Host "  [OK] Found Python 3.10: $version" -ForegroundColor Green
            break
        }
    } catch {
        continue
    }
}

# If not found, try py -3.10
if (!$PY_FOUND) {
    try {
        $version = py -3.10 --version 2>&1 | Out-String
        if ($version -match "Python 3\.10") {
            $PY_BIN = "py -3.10"
            $PY_FOUND = $true
            Write-Host "  [OK] Found Python 3.10 via py launcher: $version" -ForegroundColor Green
        }
    } catch {
        # Not found
    }
}

if (!$PY_FOUND) {
    Write-Host "  [WARN] Python 3.10 not found. Installing..." -ForegroundColor Yellow
    
    if ($PKG_MANAGER -eq "winget") {
        # Install Python 3.10 specifically
        winget install --id Python.Python.3.10 --accept-package-agreements --accept-source-agreements --silent
    } else {
        choco install python310 -y
    }
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    # Retry detection
    Start-Sleep -Seconds 2
    try {
        $version = py -3.10 --version 2>&1 | Out-String
        if ($version -match "Python 3\.10") {
            $PY_BIN = "py -3.10"
            Write-Host "  [OK] Python 3.10 installed: $version" -ForegroundColor Green
        } else {
            throw "Python 3.10 not detected after install"
        }
    } catch {
        Write-Host "[ERROR] Failed to install Python 3.10" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "[3/5] Ensuring Node.js $REQUIRED_NODE_MAJOR+ and npm are available..." -ForegroundColor Cyan

$NODE_OK = $false
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node -v
    $nodeMajor = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    if ($nodeMajor -ge $REQUIRED_NODE_MAJOR) {
        Write-Host "  [OK] Found Node.js $nodeVersion (npm v$(npm -v))" -ForegroundColor Green
        $NODE_OK = $true
    } else {
        Write-Host "  [WARN] Node.js v$nodeMajor found but v$REQUIRED_NODE_MAJOR+ required" -ForegroundColor Yellow
    }
}

if (!$NODE_OK) {
    Write-Host "  -> Installing Node.js $REQUIRED_NODE_MAJOR LTS..."
    
    if ($PKG_MANAGER -eq "winget") {
        # Uninstall old versions
        try { winget uninstall --id OpenJS.NodeJS --silent } catch {}
        # Install Node 20 LTS
        winget install --id OpenJS.NodeJS.LTS --accept-package-agreements --accept-source-agreements --silent
    } else {
        choco uninstall nodejs -y 2>$null
        choco install nodejs-lts -y
    }
    
    # Refresh PATH
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    
    Start-Sleep -Seconds 2
    if (!(Get-Command node -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] Node.js installation failed" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "  [OK] Node.js $(node -v) installed (npm v$(npm -v))" -ForegroundColor Green
}

Write-Host ""
Write-Host "[4/5] Creating Python virtual environment and installing dependencies..." -ForegroundColor Cyan

if (!(Test-Path ".venv")) {
    Write-Host "  -> Creating .venv with $PY_BIN..."
    if ($PY_BIN -match "^py ") {
        & py -3.10 -m venv .venv
    } else {
        & $PY_BIN -m venv .venv
    }
}

Write-Host "  -> Activating venv and upgrading pip..."
& .\.venv\Scripts\Activate.ps1

python -m pip install --upgrade pip --quiet

if (Test-Path "requirements.txt") {
    Write-Host "  -> Installing Python packages from requirements.txt..."
    python -m pip install -r requirements.txt
} else {
    Write-Host "  [WARN] No requirements.txt found - skipping Python package install" -ForegroundColor Yellow
}

deactivate

Write-Host ""
Write-Host "[5/5] Validating installation..." -ForegroundColor Cyan

$ERRORS = 0

# Validate Python
try {
    $pyVersion = python --version 2>&1 | Out-String
    Write-Host "  [OK] python: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "  [ERROR] python command not found" -ForegroundColor Red
    $ERRORS++
}

# Validate Node
if (Get-Command node -ErrorAction SilentlyContinue) {
    $nodeVersion = node -v
    $nodeMajor = [int]($nodeVersion -replace 'v(\d+)\..*', '$1')
    if ($nodeMajor -ge $REQUIRED_NODE_MAJOR) {
        Write-Host "  [OK] node: $nodeVersion" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] node v$nodeMajor < v$REQUIRED_NODE_MAJOR required" -ForegroundColor Red
        $ERRORS++
    }
} else {
    Write-Host "  [ERROR] node command not found" -ForegroundColor Red
    $ERRORS++
}

# Validate npm
if (Get-Command npm -ErrorAction SilentlyContinue) {
    Write-Host "  [OK] npm: v$(npm -v)" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] npm command not found" -ForegroundColor Red
    $ERRORS++
}

# Validate venv
if (Test-Path ".venv") {
    Write-Host "  [OK] .venv created" -ForegroundColor Green
} else {
    Write-Host "  [ERROR] .venv not created" -ForegroundColor Red
    $ERRORS++
}

Write-Host ""
if ($ERRORS -eq 0) {
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  ALL PREREQUISITES INSTALLED SUCCESSFULLY" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. Review config\relay.yaml for cluster topology"
    Write-Host "  2. Launch cluster: .\The_Commander.bat"
    Write-Host ""
    Write-Host "For headless backend only:" -ForegroundColor Cyan
    Write-Host "  .\.venv\Scripts\Activate.ps1"
    Write-Host "  python main.py commander-gui-dashboard --host 0.0.0.0 --port 8002"
    Write-Host ""
    exit 0
} else {
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  INSTALLATION INCOMPLETE - $ERRORS errors found" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    exit 1
}
