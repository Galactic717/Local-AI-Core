@echo off
REM ============================================
REM STOP ALL SERVICES - Local AI Assistant
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   LOCAL AI ASSISTANT - Stopping Services
echo ========================================
echo.

REM --- Emergency unload all models ---
echo [1/3] Unloading all models...
curl -s -X POST http://localhost:8004/unload/all >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Models unloaded
) else (
    echo WARNING: Could not unload models
)
timeout /t 2 /nobreak >nul
echo.

REM --- Stop services by window title ---
echo [2/3] Stopping services...

taskkill /F /FI "WINDOWTITLE eq LocalAI_Orchestrator*" >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Orchestrator stopped
) else (
    echo INFO: Orchestrator not running
)

taskkill /F /FI "WINDOWTITLE eq LocalAI_STT*" >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: STT service stopped
) else (
    echo INFO: STT service not running
)

taskkill /F /FI "WINDOWTITLE eq LocalAI_TTS*" >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: TTS service stopped
) else (
    echo INFO: TTS service not running
)

taskkill /F /FI "WINDOWTITLE eq LocalAI_Image*" >nul 2>&1
if %errorlevel% equ 0 (
    echo OK: Image service stopped
) else (
    echo INFO: Image service not running
)

echo.

REM --- Verify ---
echo [3/3] Verifying shutdown...
timeout /t 1 /nobreak >nul

curl -s http://localhost:8004/health >nul 2>&1
if %errorlevel% neq 0 (
    echo OK: All services stopped
) else (
    echo WARNING: Some services still running
)

echo.
echo ========================================
echo   Services Stopped!
echo ========================================
echo.
pause
