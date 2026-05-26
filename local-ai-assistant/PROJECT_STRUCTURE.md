# 📁 Project Structure - Local AI Assistant

**Last Updated:** 2026-04-30  
**Version:** v1.3  

---

## 🎯 Recommended Structure

```
E:\projects\AI\local-ai-assistant\
│
├── 📁 src/                          # ← ОСНОВНИЙ КОД ПРОЕКТУ
│   ├── 📁 core/                     # Ядро системи
│   │   ├── __init__.py
│   │   ├── orchestrator.py          # VRAM Orchestrator
│   │   ├── config_loader.py         # Завантаження конфігів
│   │   └── logger.py                # Централізоване логування
│   │
│   ├── 📁 services/                 # Мікросервіси
│   │   ├── __init__.py
│   │   ├── stt_service.py           # Speech-to-Text
│   │   ├── tts_service.py           # Text-to-Speech
│   │   └── image_service.py         # Image Generation
│   │
│   ├── 📁 api/                      # API endpoints
│   │   ├── __init__.py
│   │   ├── orchestrator_api.py      # Orchestrator REST API
│   │   ├── stt_api.py               # STT endpoints
│   │   ├── tts_api.py               # TTS endpoints
│   │   └── image_api.py             # Image endpoints
│   │
│   ├── 📁 models/                   # Data models
│   │   ├── __init__.py
│   │   ├── vram_models.py           # VRAM status models
│   │   └── service_models.py        # Service request/response models
│   │
│   ├── 📁 utils/                    # Утиліти
│   │   ├── __init__.py
│   │   ├── vram_monitor.py          # VRAM моніторинг
│   │   └── health_check.py          # Health checks
│   │
│   └── 📁 integrations/             # Інтеграції
│       ├── __init__.py
│       ├── ollama_client.py         # Ollama API wrapper
│       └── webui_connector.py       # Open WebUI integration
│
├── 📁 config/                       # Конфігурації
│   ├── ollama_config.yaml
│   ├── services_config.yaml
│   └── logging_config.yaml
│
├── 📁 scripts/                      # Скрипти запуску/тестування
│   ├── start_services.bat           # Запуск всіх сервісів
│   ├── stop_services.bat            # Зупинка сервісів
│   ├── dev_start.bat                # Режим розробки (VS Code)
│   └── test_endpoints.py            # Тестування API
│
├── 📁 tests/                        # Тести
│   ├── __init__.py
│   ├── test_orchestrator.py
│   ├── test_stt.py
│   └── test_integration.py
│
├── 📁 logs/                         # Логи
│   ├── orchestrator.log
│   ├── stt_service.log
│   └── errors.log
│
├── 📁 data/                         # Дані
│   ├── audio/                       # Аудіо файли
│   ├── images/                      # Згенеровані зображення
│   └── cache/                       # Кеш
│
├── 📁 models/                       # ML моделі
│   ├── whisper/                     # Whisper models
│   ├── piper/                       # Piper TTS models
│   └── sd_turbo/                    # Stable Diffusion
│
├── 📁 docs/                         # Документація
│   ├── API.md
│   ├── ARCHITECTURE.md
│   └── DEPLOYMENT.md
│
├── 📁 venv/                         # Virtual environment
│
├── .env                             # Environment variables
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
└── PHASE1_TEST_RESULTS.md

```

---

## 🔄 Migration Plan

### Current State (Flat Structure)
```
services/
  ├── orchestrator.py          # ← Основний код
  └── stt_service.py           # ← Основний код

scripts/
  ├── health_check.py          # ← Утиліта
  └── monitor_vram.py          # ← Утиліта
```

### Target State (Organized Structure)
```
src/
  ├── core/
  │   └── orchestrator.py      # ← Перенести з services/
  │
  ├── services/
  │   └── stt_service.py       # ← Перенести з services/
  │
  └── utils/
      ├── health_check.py      # ← Перенести з scripts/
      └── vram_monitor.py      # ← Перенести з scripts/
```

---

## 🎯 Benefits

### 1. VS Code Development
```
src/                    # ← Відкриваєш цю папку в VS Code
  ├── core/            # ← Чітко бачиш ядро системи
  ├── services/        # ← Всі сервіси в одному місці
  └── api/             # ← API endpoints окремо
```

### 2. Import Structure
```python
# Чіткі імпорти
from src.core.orchestrator import VRAMOrchestrator
from src.services.stt_service import STTService
from src.utils.vram_monitor import VRAMMonitor
```

### 3. Testing
```python
# Легко тестувати
from src.core.orchestrator import VRAMOrchestrator

def test_orchestrator():
    orch = VRAMOrchestrator()
    assert orch.get_vram_usage_mb() > 0
```

### 4. Deployment
```bash
# Запуск як додаток
python -m src.core.orchestrator

# Або через uvicorn
uvicorn src.api.orchestrator_api:app --host 0.0.0.0 --port 8004
```

---

## 📝 Migration Steps

### Phase 1: Create Structure
1. ✅ Create `src/` directory
2. ✅ Create subdirectories (core, services, api, utils, models, integrations)
3. ✅ Add `__init__.py` to all packages

### Phase 2: Move Files
1. Move `services/orchestrator.py` → `src/core/orchestrator.py`
2. Move `services/stt_service.py` → `src/services/stt_service.py`
3. Move `scripts/health_check.py` → `src/utils/health_check.py`
4. Move `scripts/monitor_vram.py` → `src/utils/vram_monitor.py`

### Phase 3: Update Imports
1. Update all imports in moved files
2. Update `start_services.bat` paths
3. Update test files

### Phase 4: VS Code Setup
1. Create `.vscode/settings.json`
2. Configure Python path
3. Add launch configurations

---

## 🚀 VS Code Configuration

### .vscode/settings.json
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/Scripts/python.exe",
  "python.analysis.extraPaths": [
    "${workspaceFolder}/src"
  ],
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": [
    "tests"
  ],
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "venv/": true
  }
}
```

### .vscode/launch.json
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Orchestrator",
      "type": "python",
      "request": "launch",
      "module": "src.core.orchestrator",
      "console": "integratedTerminal",
      "env": {
        "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"
      }
    },
    {
      "name": "STT Service",
      "type": "python",
      "request": "launch",
      "module": "src.services.stt_service",
      "console": "integratedTerminal"
    }
  ]
}
```

---

## 🎯 Next Steps

1. **Створити структуру `src/`**
2. **Перенести файли**
3. **Оновити імпорти**
4. **Налаштувати VS Code**
5. **Протестувати запуск**

---

**Ready to migrate?** Підтверди і я почну реорганізацію! 🚀
