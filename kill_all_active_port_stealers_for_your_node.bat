@echo off
setlocal enabledelayedexpansion

:: GILLSYSTEMS COMMANDER OS // TACTICAL PORT CLEARANCE (Windows)
:: This script kills any processes holding onto the Commander ports.

echo ===================================================================
echo   🛡️  GILLSYSTEMS COMMANDER OS - Tactical Port Clearance (Windows)
echo ===================================================================

set PORTS=8000 8001 8002 8003 5173 5174 5175

echo [1/2] Terminating processes on critical ports...
for %%p in (%PORTS%) do (
    for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":%%p" ^| findstr "LISTENING"') do (
        echo   ✓ Clearing Port: %%p (PID: %%a^)
        taskkill /F /PID %%a >nul 2>&1
    )
)

echo [2/2] Cleaning up remaining Python/Vite instances...
taskkill /F /IM python.exe /T >nul 2>&1
taskkill /F /IM node.exe /T >nul 2>&1

echo ===================================================================
echo   ✅ SYSTEM CLEARANCE COMPLETE
echo ===================================================================
pause
