@echo off
SETLOCAL EnableDelayedExpansion
chcp 65001 >nul

title GILLSYSTEMS COMMANDER OS // UNIFIED CONSOLE [v1.2.19]
echo.
echo  ============================================================
echo     GILLSYSTEMS COMMANDER OS: UNIFIED CONSOLE [v1.2.19]
echo     PRIME DIRECTIVE: ALWAYS VERIFY REQUIREMENTS
echo  ============================================================

set "ROOT_DIR=%~dp0"
set "BIN_DIR=%ROOT_DIR%.bin"
set "RUNTIME_DIR=%ROOT_DIR%.bin\python"
set "VENV_DIR=%ROOT_DIR%.venv"
set "GUI_DIR=%ROOT_DIR%commander_os\interfaces\gui"

:: -----------------------------------------------------------------------------
:: STAGE 1: RUNTIME CHECK (Silent)
:: -----------------------------------------------------------------------------
if not exist "%RUNTIME_DIR%\python.exe" (
    echo [ALERT] Deploying Portable Runtime...
    if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
    if not exist "%BIN_DIR%\installer.exe" curl -L -o "%BIN_DIR%\installer.exe" https://www.python.org/ftp/python/3.10.11/python-3.10.11-amd64.exe
    start "" /wait "%BIN_DIR%\installer.exe" /passive InstallAllUsers=0 TargetDir="%RUNTIME_DIR%" PrependPath=0 Include_test=0
    del "%BIN_DIR%\installer.exe"
)
set "TARGET_PYTHON=%RUNTIME_DIR%\python.exe"

:: -----------------------------------------------------------------------------
:: STAGE 2: BUILD & VERIFY
:: -----------------------------------------------------------------------------
echo.
echo [STAGE 2] DEPENDENCY SYNC...

set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

:: Create venv if missing
if not exist "%VENV_PYTHON%" (
    echo [ACTION] Initializing Venv...
    "%TARGET_PYTHON%" -I -m venv "%VENV_DIR%"
    "%VENV_DIR%\Scripts\python.exe" -I -m ensurepip --default-pip
    "%VENV_DIR%\Scripts\python.exe" -I -m pip install --upgrade pip
)

:: ALWAYS run install to catch missing libs (like 'rich')
:: Using --no-warn-script-location to keep log clean
"%VENV_PYTHON%" -I -m pip install --no-cache-dir --only-binary :all: -r "%ROOT_DIR%requirements.txt" >nul 2>&1
if !errorlevel! neq 0 (
    echo [WARNING] Retrying install with standard mode...
    "%VENV_PYTHON%" -I -m pip install -r "%ROOT_DIR%requirements.txt" || (
        echo [CRITICAL] Dependency Install Failed.
        pause
        exit /b
    )
)
echo [SUCCESS] Dependencies Synchronized.

:: -----------------------------------------------------------------------------
:: STAGE 3: HUD (Background Launch)
:: -----------------------------------------------------------------------------
echo.
echo [STAGE 3] LAUNCHING STRATEGIC DASHBOARD (BACKGROUND)...
cd /d "%GUI_DIR%"
if not exist node_modules call npm install --loglevel error --no-audit

:: Launch Vite Minimized
start "COMMANDER_HUD" /min cmd /c "npm run dev"
cd /d "%ROOT_DIR%"

:: -----------------------------------------------------------------------------
:: STAGE 4: BACKEND (Foreground)
:: -----------------------------------------------------------------------------
echo.
echo [STAGE 4] ENGAGING ORCHESTRATION HUB...
echo.
echo  ============================================================
echo     GILLSYSTEMS COMMANDER OS is ACTIVE
echo  ============================================================
echo.
echo [INFO] Access Strategic Dashboard: http://localhost:5173
echo [INFO] Ctrl+C to Terminate Backend.
echo.

set "PYTHONPATH=%ROOT_DIR%"
"%VENV_PYTHON%" main.py commander-gui-dashboard

:: If we drop here, catch the error
echo.
echo [CRITICAL] HUB FAILURE.
pause
