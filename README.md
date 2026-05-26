# 🤖 Local AI Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Electron](https://img.shields.io/badge/Electron-Latest-brightgreen.svg)](https://www.electronjs.org/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_AI-orange.svg)](https://ollama.ai/)

> **A powerful, private, and modular AI ecosystem running entirely on your local machine.**

Local AI Assistant is a sophisticated orchestration platform that integrates LLMs (via Ollama), Speech-to-Text (STT), Text-to-Speech (TTS), and Image Generation into a unified, agentic interface. Built for performance and privacy, it bypasses the cloud to give you full control over your intelligence.

---

## ⚡ Quick Start

### The "One-Click" Experience (Windows)
Simply run the bootstrap script to launch the entire ecosystem:
```bash
./LAUNCH_CODEX.bat
```

---

## 🏗️ Architecture

```mermaid
graph TD
    User([User Interface]) <--> UI[Local AI UI - Electron/Vite]
    UI <--> Router[Brain Router - Orchestrator]
    
    subgraph Services [Intelligence Layer]
        Router <--> LLM[Ollama LLM]
        Router <--> STT[Speech-to-Text]
        Router <--> TTS[Text-to-Speech]
        Router <--> IMG[Image Generation]
    end
    
    subgraph Hardware [Hardware Acceleration]
        LLM --- GPU[NVIDIA CUDA]
        STT --- GPU
        IMG --- GPU
    end
```

---

## 🌟 Key Features

| Component | Technology | Capability |
| :--- | :--- | :--- |
| **Orchestrator** | Python / FastAPI | Intelligent routing & service management |
| **Brain UI** | React / Electron | Modern, responsive dashboard |
| **Intelligence** | Ollama | Llama 3, Mistral, and custom models |
| **Perception** | OpenAI Whisper | High-accuracy local speech recognition |
| **Vocal** | Edge-TTS / Piper | Natural-sounding local speech synthesis |
| **Creativity** | Stable Diffusion | Local high-resolution image generation |

---

## 📁 Project Structure

*   **`local-ai-assistant/`**: The neural core. Python-based microservices and orchestration.
*   **`local-ai-ui/`**: The visual cortex. Electron/React dashboard for interacting with the assistant.
*   **`scripts/`**: Automation and deployment utilities.
*   **`data/`**: Local memory and processing storage.

---

## 🛠️ Development

### Prerequisites
- Python 3.10+
- Node.js 18+
- Ollama (installed and running)
- NVIDIA GPU (recommended for acceleration)

### Manual Setup
1. **Core:** Navigate to `local-ai-assistant/`, create venv, and `pip install -r requirements.txt`.
2. **UI:** Navigate to `local-ai-ui/`, run `npm install`.

For detailed instructions, see the READMEs in each sub-folder.

---

## 🤝 Contributing

We welcome contributions! Please see [CLAUDE.md](./CLAUDE.md) for project standards and development workflows.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
