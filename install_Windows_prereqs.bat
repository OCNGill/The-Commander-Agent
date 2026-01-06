@echo off
setlocal

echo.
echo ============================================================
echo   GILLSYSTEMS COMMANDER OS - Windows Prerequisites Installer
echo ============================================================
echo.

REM Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges.
    echo.
    echo Right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo Running prerequisite installer...
echo.

REM Run the PowerShell script with bypass execution policy
powershell.exe -ExecutionPolicy Bypass -File "%~dp0scripts\windows_prereqs.ps1"

if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Installation failed with exit code %errorLevel%
    echo.
    pause
    exit /b %errorLevel%
)

echo.
echo ============================================================
echo   Installation completed successfully!
echo ============================================================
echo.
pause
