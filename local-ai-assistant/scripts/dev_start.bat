@echo off
REM ============================================
REM DEV MODE - Start Orchestrator for VS Code
REM ============================================

setlocal enabledelayedexpansion

echo.
echo ========================================
echo   DEV MODE - Orchestrator Only
echo ========================================
echo.

REM --- Get script directory ---
set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
cd /d "%PROJECT_ROOT%"

REM PATCH v1.3: WDDM Fix
set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
set PYTHONPATH=%PROJECT_ROOT%

echo [1/3] Environment configured
echo   PYTORCH_CUDA_ALLOC_CONF=%PYTORCH_CUDA_ALLOC_CONF%
echo   PYTHONPATH=%PYTHONPATH%
echo.

REM --- Check venv ---
echo [2/3] Checking virtual environment...
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found!
    pause
    exit /b 1
)
echo OK: venv found
echo.

REM --- Start Orchestrator ---
echo [3/3] Starting Orchestrator (DEV MODE)...
echo.
echo TIP: Open VS Code and use F5 to debug
echo      Or run: venv\Scripts\python -m uvicorn src.core.orchestrator:app --reload
echo.

start "LocalAI_Orchestrator_DEV" cmd /k "cd /d "%PROJECT_ROOT%" && venv\Scripts\python -m uvicorn src.core.orchestrator:app --host 0.0.0.0 --port 8004 --reload"

timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   DEV MODE Started!
echo ========================================
echo.
echo Orchestrator: http://localhost:8004
echo Status:       http://localhost:8004/status
echo Docs:         http://localhost:8004/docs
echo.
echo Press any key to return...
pause >nul
