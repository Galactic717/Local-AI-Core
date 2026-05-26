@echo off
REM ============================================
REM START ALL SERVICES - Local AI Assistant v1.4
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   LOCAL AI ASSISTANT - Starting Services
echo ========================================
echo.

REM --- Get script directory ---
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"

REM WDDM Fix & CUDA Alloc Conf
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

REM --- Check Python ---
echo [1/6] Checking Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo OK: Python found

REM --- Check Ollama ---
echo [2/6] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Ollama not responding!
    echo Starting Ollama...
    start "Ollama" ollama serve
    timeout /t 5 /nobreak >nul
)
echo OK: Ollama running

REM --- Start Orchestrator ---
echo [3/6] Starting Orchestrator...
start "LocalAI_Orchestrator" cmd /k "cd /d "%PROJECT_ROOT%" && venv\Scripts\python -m src.core.orchestrator"
timeout /t 3 /nobreak >nul
echo OK: Orchestrator started (port 8004)

REM --- Start STT Service ---
echo [4/6] Starting STT Service...
start "LocalAI_STT" cmd /k "cd /d "%PROJECT_ROOT%" && venv\Scripts\python -m src.services.stt_service"
timeout /t 2 /nobreak >nul
echo OK: STT Service started (port 8001)

REM --- Start TTS Service ---
echo [5/6] Starting TTS Service...
start "LocalAI_TTS" cmd /k "cd /d "%PROJECT_ROOT%" && venv\Scripts\python -m src.services.tts_service"
timeout /t 2 /nobreak >nul
echo OK: TTS Service started (port 8002)

REM --- Start Image Service ---
echo [6/6] Starting Image Service...
start "LocalAI_Image" cmd /k "cd /d "%PROJECT_ROOT%" && venv\Scripts\python -m src.services.image_service"
timeout /t 2 /nobreak >nul
echo OK: Image Service started (port 8003)

echo.
echo ========================================
echo   All Services Started!
echo ========================================
echo.
echo Orchestrator: http://localhost:8004
echo STT Service:  http://localhost:8001
echo TTS Service:  http://localhost:8002
echo Image Service: http://localhost:8003
echo.
echo Press any key to return...
pause >nul
