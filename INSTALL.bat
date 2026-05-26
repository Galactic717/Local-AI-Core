@echo off
setlocal enabledelayedexpansion

echo ========================================================
echo   Local AI Assistant - Full System Installer
echo ========================================================
echo.

:: 1. Check Prerequisites
echo [1/4] Checking prerequisites...
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH.
    exit /b 1
)
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ERROR: Node.js is not installed or not in PATH.
    exit /b 1
)
echo OK: Python and Node.js found.

:: 2. Setup Backend
echo.
echo [2/4] Setting up Backend (local-ai-assistant)...
cd local-ai-assistant
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)
echo Installing Python dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
if not exist .env (
    if exist .env.example (
        echo Creating .env from .env.example...
        copy .env.example .env
    )
)
deactivate
cd ..

:: 3. Setup Frontend
echo.
echo [3/4] Setting up Frontend (local-ai-ui)...
cd local-ai-ui
echo Running npm install...
call npm install
cd ..

:: 4. Restore Models
echo.
echo [4/4] Do you want to download AI models now? (Ollama required)
set /p models="Download models? (y/n): "
if /i "%models%"=="y" (
    call scripts\restore_models.bat
)

echo.
echo ========================================================
echo   Installation Complete!
echo ========================================================
echo To start the assistant, run: LAUNCH_CODEX.bat
echo ========================================================
pause
