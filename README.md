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

## 🛠️ Setup & Restoration (Zero to Hero)

Because AI models and virtual environments are large, they are excluded from this repository. Follow these steps to fully restore the project on a new machine.

### Prerequisites
- Python 3.10+
- Node.js 18+
- [Ollama](https://ollama.ai/) (installed and running)
- NVIDIA GPU (RTX 3060 6GB+ highly recommended)

### 1. Clone & Initialize
```bash
git clone https://github.com/Galactic717/local-ai-assistant.git
cd local-ai-assistant
```

### 2. Restore Intelligence (Models)
The orchestrator relies on specific LLMs. Run the restoration script to pull them via Ollama:
```bash
# Windows
.\scripts\restore_models.bat
```
*(This will download Qwen2.5, Phi-4-mini, and DeepSeek-R1).*
*Note: STT and Image Generation models are downloaded automatically by HuggingFace upon their first run.*

### 3. Setup Backend (Core)
```bash
cd local-ai-assistant
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env  # Edit .env with your specific paths/ports
```

### 4. Setup Frontend (UI)
```bash
cd ../local-ai-ui
npm install
```

### 5. Launch
Return to the root directory and use the "One-Click" script:
```bash
./LAUNCH_CODEX.bat
```

---

## 🤝 Contributing

We welcome contributions! Please see [CLAUDE.md](./CLAUDE.md) for project standards and development workflows.

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
