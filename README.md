# Aether: Local Intelligence Cortex

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Privacy](https://img.shields.io/badge/Privacy-100%25_Local-blue.svg)](#)

> **A powerful, private, and modular AI ecosystem running entirely on your local hardware.**

**Aether** is a sophisticated orchestration platform that integrates Large Language Models (LLMs), Speech-to-Text (STT), Text-to-Speech (TTS), and Image Generation into a unified, agentic interface. It bypasses the cloud entirely, providing zero-latency intelligence with absolute privacy.

---

## ⚡ Architecture

Aether uses a **Neural Router** to dynamically select the best local model based on the complexity and domain of your query.

*   **Logic:** Qwen 3.5 (9B) / DeepSeek R1 (8B)
*   **Coding:** Qwen 2.5 Coder (32B)
*   **Perception:** OpenAI Whisper (Local CUDA)
*   **Vocal:** Edge-TTS / Piper
*   **Vision:** Stable Diffusion XL (Local)

---

## 🏗️ Quick Start

### One-Click Launch (Windows)
```bash
.\LAUNCH_AETHER.bat
```

### Manual Setup
1. **Restore Models:** `.\scripts\restore_models.bat`
2. **Launch Backend:** `cd local-ai-assistant && python brain_router.py`
3. **Launch UI:** `cd local-ai-ui && npm run dev`

---

## 📂 Project Structure

*   **`local-ai-assistant/`**: The neural core (Python/FastAPI).
*   **`local-ai-ui/`**: The visual cortex (React/Electron).
*   **`scripts/`**: Automation and model management.

---

## 📜 Technical Philosophy

Aether is built on the principle of **Data Sovereignty**. In an era of cloud-centric AI, Aether empowers the individual to own their cognitive tools. It is optimized for NVIDIA hardware, utilizing CUDA and TensorRT for maximum performance.

---
*Developed by Гліб Сергійович Степанов.*
