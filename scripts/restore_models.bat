@echo off
echo ========================================================
echo   Local AI Assistant - Model Restoration Script
echo ========================================================
echo.
echo This script will download the necessary Ollama models
echo required for the Brain Router to function.
echo.
echo Make sure Ollama is installed and running!
echo.
pause

echo.
echo [1/3] Pulling Qwen 2.5 (7B)...
ollama pull qwen2.5:7b

echo.
echo [2/3] Pulling Phi-4 Mini...
ollama pull phi4-mini:latest

echo.
echo [3/3] Pulling DeepSeek R1 (8B)...
ollama pull deepseek-r1:8b

echo.
echo ========================================================
echo   Note for STT, TTS, and Image Generation Models:
echo ========================================================
echo - STT (Whisper) and Image Gen (Stable Diffusion) models
echo   will be downloaded automatically by the Python scripts 
echo   (HuggingFace Hub) upon their first run.
echo - TTS (Piper) ONNX models need to be placed in:
echo   local-ai-assistant/models/piper/
echo ========================================================
echo.
echo Restoration complete!
pause
