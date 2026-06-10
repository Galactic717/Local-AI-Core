@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   CODEX AI ASSISTANT - MASTER STARTUP v1.5
echo ============================================

REM 1. Очищення завислих процесів
echo [1/4] Cleaning up old processes...
taskkill /F /IM python.exe /T >nul 2>&1
echo OK: System ports cleared.

REM 2. Перевірка Ollama
echo [2/4] Checking Ollama...
curl -s http://localhost:11434/api/tags >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Ollama is NOT running. Starting it...
    start "Ollama" /min ollama serve
    timeout /t 5 >nul
)
echo OK: Ollama ready.

REM 3. Запуск Backend сервісів
echo [3/4] Starting AI Backend Services...
cd /d E:\projects\AI\local-ai-assistant

set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True

REM Запуск Оркестратора (VRAM менеджер)
start "AI: Orchestrator" /min venv\Scripts\python -m src.core.orchestrator
timeout /t 3 >nul

REM Запуск Brain Router (Інтелектуальний вибір моделей)
start "AI: Brain Router" /min venv\Scripts\python -m src.services.brain_router
timeout /t 2 >nul

REM Запуск STT (Speech-to-Text)
start "AI: STT Service" /min venv\Scripts\python -m src.services.stt_service

REM Запуск TTS (Text-to-Speech)
start "AI: TTS Service" /min venv\Scripts\python -m src.services.tts_service

REM Запуск Image Service (Stable Diffusion)
start "AI: Image Service" /min venv\Scripts\python -m src.services.image_service

echo OK: Backend services are starting in background.

REM 4. Запуск Frontend (React UI)
echo [4/4] Starting Codex UI...
cd /d E:\projects\AI\local-ai-ui
start "AI: Codex UI" /min npm run dev

echo.
echo ============================================
echo   SYSTEM READY!
echo ============================================
echo   Codex Interface: http://localhost:5173
echo   Brain Router:    http://localhost:8000
echo   Orchestrator:    http://localhost:8004
echo   Ollama API:      http://localhost:11434
echo ============================================
echo.
echo Press any key to STOP ALL services and exit...
pause >nul

REM Зупинка всього при закритті
taskkill /F /IM python.exe /T >nul 2>&1
echo System stopped.
