@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   LOCAL AI ASSISTANT - MASTER STARTUP v1.4
echo ============================================

REM 1. Очищення завислих процесів (Cleanup)
echo [1/3] Cleaning up old processes...
taskkill /F /IM python.exe /T >nul 2>&1
echo OK: Ports cleared.

REM 2. Запуск Backend сервісів
echo [2/3] Starting Backend Services...
cd /d E:\projects\AI\local-ai-assistant

start "AI: Orchestrator" /min venv\Scripts\python -m src.core.orchestrator
timeout /t 2 >nul
start "AI: STT Service" /min venv\Scripts\python -m src.services.stt_service
start "AI: TTS Service" /min venv\Scripts\python -m src.services.tts_service
start "AI: Image Service" /min venv\Scripts\python -m src.services.image_service

echo OK: Backend services are starting in background.

REM 3. Запуск Frontend (Codex UI)
echo [3/3] Starting Codex UI...
cd /d E:\projects\AI\local-ai-ui
start "AI: Codex UI" /min npm run dev

echo.
echo ============================================
echo   SYSTEM READY!
echo ============================================
echo   Dashboard: http://localhost:5173
echo   Orchestrator: http://localhost:8004
echo   Ollama: http://localhost:11434
echo ============================================
echo.
echo Press any key to stop ALL services and exit...
pause >nul

REM Зупинка всього при закритті
taskkill /F /IM python.exe /T >nul 2>&1
echo Done.
