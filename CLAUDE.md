# CLAUDE.md - Rules of Engagement

## 🚀 Project Overview
**Local AI Assistant** is a modular, local-first AI ecosystem.
- **Backend**: Python 3.10+, FastAPI, Ollama.
- **Frontend**: Electron, React, Vite, Tailwind CSS.

## 🛠 Build & Development Commands

### Backend (local-ai-assistant)
- **Activate Venv**: `venv\Scripts\activate` (Windows)
- **Install Deps**: `pip install -r requirements.txt`
- **Run Orchestrator**: `python brain_router.py`
- **Run Tests**: `pytest`

### Frontend (local-ai-ui)
- **Install Deps**: `npm install`
- **Dev Mode**: `npm run dev`
- **Build**: `npm run build`
- **Lint**: `npm run lint`

## 📏 Coding Standards

### Python (Backend)
- Use type hints for all function signatures.
- Follow PEP 8 style guidelines.
- Prefer asynchronous operations (FastAPI/asyncio) for service communication.
- Log errors comprehensively using the `logging` module.

### TypeScript/React (Frontend)
- Use functional components and Hooks.
- Strict TypeScript: Avoid `any`, use explicit interfaces/types.
- Tailwind CSS for styling.
- Follow Vite/Electron best practices for main/renderer process separation.

## 🔄 Workflow
1. **Research**: Check `PROJECT_STRUCTURE.md` in subdirectories before making changes.
2. **Implement**: Keep components modular and decoupled.
3. **Test**: Ensure new features are covered by tests.
4. **Document**: Update relevant README files if API or structure changes.

## 📁 Key File Map
- `local-ai-assistant/src/`: Core backend logic.
- `local-ai-ui/src/`: Frontend React components.
- `LAUNCH_CODEX.bat`: Root entry point for the entire system.
