# 🚀 Local AI Assistant - Quick Start Guide

**Version:** 1.3  
**Last Updated:** 2026-04-30  

---

## 📁 Project Structure

```
E:\projects\AI\local-ai-assistant\
│
├── 📁 src/                      # ← ОСНОВНИЙ КОД (відкривай в VS Code)
│   ├── core/                    # Orchestrator
│   ├── services/                # STT, TTS, Image
│   ├── utils/                   # Health checks, monitoring
│   └── __init__.py
│
├── 📁 config/                   # Конфігурації
├── 📁 scripts/                  # Скрипти запуску
├── 📁 tests/                    # Тести
├── 📁 logs/                     # Логи
└── 📁 venv/                     # Virtual environment
```

---

## 🎯 Режими роботи

### 1️⃣ Режим розробки (VS Code)

**Для розробки та дебагу:**

```bash
# Відкрий проект у VS Code
code E:\projects\AI\local-ai-assistant

# Або запусти через скрипт
scripts\dev_start.bat
```

**У VS Code:**
- Натисни `F5` → вибери "🎯 Orchestrator (Main)"
- Або `Ctrl+Shift+D` → Debug panel → вибери конфігурацію

**Доступні конфігурації:**
- 🎯 Orchestrator (Main) - порт 8004
- 🎤 STT Service - порт 8001
- 🔍 Health Check
- 📊 VRAM Monitor
- 🧪 Run Tests

---

### 2️⃣ Режим production (localhost)

**Для повноцінного запуску:**

```bash
# Запустити всі сервіси
scripts\start_services.bat

# Зупинити всі сервіси
scripts\stop_services.bat
```

**Доступні endpoints:**
- http://localhost:8004 - Orchestrator
- http://localhost:8004/docs - API документація
- http://localhost:8004/status - VRAM статус

---

## 🔧 Налаштування VS Code

### Встановлені конфігурації:

✅ `.vscode/launch.json` - Debug конфігурації  
✅ `.vscode/settings.json` - Python налаштування  

### Python Path:
```
PYTHONPATH = E:\projects\AI\local-ai-assistant
```

### Imports:
```python
from src.core.orchestrator import VRAMOrchestrator
from src.services.stt_service import STTService
from src.utils.health_check import check_health
```

---

## 🧪 Тестування

### Запуск тестів:

```bash
# Через VS Code
F5 → "🧪 Run Tests"

# Через командний рядок
venv\Scripts\activate
pytest tests/ -v
```

### Ручне тестування API:

```bash
# Status
curl http://localhost:8004/status

# Health
curl http://localhost:8004/health

# Prepare LLM
curl -X POST http://localhost:8004/prepare/llm \
  -H "Content-Type: application/json" \
  -d '{"model_name":"qwen2.5:7b","required_mb":3500}'
```

---

## 📂 Структура коду

### Core (src/core/)
- `orchestrator.py` - VRAM Orchestrator v1.3
  - Threading.Lock для race conditions
  - WDDM Fix (expandable_segments)
  - Оптимізований gc.collect()

### Services (src/services/)
- `stt_service.py` - Speech-to-Text (Phase 2)
- `tts_service.py` - Text-to-Speech (Phase 3) - TODO
- `image_service.py` - Image Generation (Phase 4) - TODO

### Utils (src/utils/)
- `health_check.py` - Health checks
- `vram_monitor.py` - VRAM monitoring

---

## 🎨 VS Code Extensions (Recommended)

- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Black Formatter (ms-python.black-formatter)
- Python Debugger (ms-python.debugpy)

---

## 🚦 Current Status

| Component | Status | Port |
|-----------|--------|------|
| Orchestrator v1.3 | ✅ Ready | 8004 |
| STT Service | 🚧 Phase 2 | 8001 |
| TTS Service | ⏳ Phase 3 | 8002 |
| Image Service | ⏳ Phase 4 | 8003 |

---

## 📝 Next Steps

1. ✅ Phase 1 Complete - Orchestrator v1.3
2. 🚧 Phase 2 - STT Integration
3. ⏳ Phase 3 - TTS Integration
4. ⏳ Phase 4 - Image Generation

---

## 🔗 Links

- **Документація:** `E:\Obsidian\Claude\Local AI Assistant Wiki`
- **Тести Phase 1:** `PHASE1_TEST_RESULTS.md`
- **Структура:** `PROJECT_STRUCTURE.md`

---

**Ready to code!** 🚀

Відкрий VS Code, натисни F5 і почни розробку!
