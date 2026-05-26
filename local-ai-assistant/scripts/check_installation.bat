@echo off
REM ============================================
REM Installation Check Script
REM ============================================

echo.
echo ========================================
echo   LOCAL AI ASSISTANT - Installation Check
echo ========================================
echo.

REM --- Python Version ---
echo [1/6] Checking Python version...
python --version
if %errorlevel% neq 0 (
    echo ERROR: Python not found!
    exit /b 1
)
echo.

REM --- Virtual Environment ---
echo [2/6] Checking virtual environment...
if exist "venv\Scripts\python.exe" (
    echo OK: Virtual environment found
) else (
    echo WARNING: Virtual environment not found. Run: python -m venv venv
)
echo.

REM --- CUDA Toolkit ---
echo [3/6] Checking CUDA toolkit...
nvcc --version 2>nul
if %errorlevel% neq 0 (
    echo WARNING: CUDA toolkit not found or not in PATH
) else (
    echo OK: CUDA toolkit detected
)
echo.

REM --- NVIDIA GPU ---
echo [4/6] Checking NVIDIA GPU...
nvidia-smi 2>nul
if %errorlevel% neq 0 (
    echo WARNING: nvidia-smi not available
) else (
    echo OK: NVIDIA GPU detected
)
echo.

REM --- Ollama ---
echo [5/6] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Ollama not responding on http://localhost:11434
    echo Make sure Ollama is running: ollama serve
) else (
    echo OK: Ollama is running
)
echo.

REM --- Python Packages ---
echo [6/6] Checking Python packages...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -c "import fastapi, uvicorn, torch, psutil" 2>nul
    if %errorlevel% neq 0 (
        echo WARNING: Some packages missing. Run: pip install -r requirements.txt
    ) else (
        echo OK: Core packages installed
        venv\Scripts\python.exe -c "import torch; print(f'PyTorch CUDA available: {torch.cuda.is_available()}')"
    )
) else (
    echo SKIP: Virtual environment not found
)
echo.

echo ========================================
echo   Check completed!
echo ========================================
echo.
pause
