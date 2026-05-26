# 🤖 Local AI Assistant - Phase 1

**Локальний AI асистент з підтримкою Ollama, STT, TTS та Image Generation**

> ⚠️ **ВАЖЛИВО**: Проект працює **ТІЛЬКИ** на native Python + Windows `.bat`. Без Docker/WSL2!

---

## 📋 Опис проекту

Local AI Assistant — це модульна система для роботи з локальними AI моделями через Ollama. Проект складається з мікросервісів (STT, TTS, Image Gen) та центрального оркестратора.

**Поточна фаза**: Phase 1 - Базова інфраструктура та оркестратор

---

## 🏗️ Структура проекту

```
local-ai-assistant/
├── config/          # Конфігураційні файли (YAML/JSON)
├── services/        # Мікросервіси (STT, TTS, Image, Orchestrator)
├── scripts/         # Утилітні скрипти (.bat для Windows)
├── logs/            # Логи сервісів
├── data/            # Дані для обробки
├── temp/            # Тимчасові файли
├── models/          # Локальні моделі (якщо потрібно)
├── .env             # Змінні оточення (створи з .env.example)
├── requirements.txt # Python залежності
└── README.md        # Цей файл
```

---

## 🚀 Швидкий старт

### 1️⃣ Створення віртуального середовища

```bash
# Windows CMD/PowerShell
python -m venv venv

# Активація (CMD)
venv\Scripts\activate.bat

# Активація (PowerShell)
venv\Scripts\Activate.ps1

# Активація (Git Bash)
source venv/Scripts/activate
```

### 2️⃣ Встановлення залежностей

```bash
# Оновлення pip
python -m pip install --upgrade pip

# Встановлення базових залежностей
pip install -r requirements.txt

# Встановлення PyTorch з CUDA 12.1 (якщо є NVIDIA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3️⃣ Налаштування середовища

```bash
# Копіювання .env.example
copy .env.example .env

# Відредагуй .env під свою систему (шляхи, порти, VRAM ліміт)
notepad .env
```

### 4️⃣ Перевірка встановлення

```bash
# Перевірка Python версії (потрібен 3.10+)
python --version

# Перевірка CUDA (якщо є GPU)
nvcc --version
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Перевірка nvidia-smi
nvidia-smi

# Перевірка Ollama
curl http://localhost:11434/api/tags
```

---

## 📦 Залежності Phase 1

- **FastAPI** - Web framework для API
- **Uvicorn** - ASGI сервер
- **psutil** - Моніторинг системних ресурсів
- **nvidia-ml-py** - Моніторинг NVIDIA GPU (VRAM, temp)
- **PyTorch** - Deep learning framework (CUDA 12.1)
- **python-dotenv** - Завантаження змінних з .env
- **requests/httpx** - HTTP клієнти
- **tenacity** - Retry logic

> **Примітка**: STT/TTS/Image залежності додаються в Phase 2-4

---

## ⚙️ Конфігурація

### VRAM Threshold
- **Поточне значення**: 5200 MB (v1.2 patch)
- **Попереднє**: 5500 MB
- Знижено для стабільності на RTX 3060 (6GB VRAM)

### Порти сервісів
- STT Service: `8001`
- TTS Service: `8002`
- Image Service: `8003`
- Orchestrator: `8004`
- WebUI: `8080`

---

## 📚 Документація

Повний Master Plan та архітектура:
- [Master Plan Wiki](https://github.com/your-repo/wiki) *(додай посилання)*
- Phase 1: Базова інфраструктура
- Phase 2: STT Service
- Phase 3: TTS Service
- Phase 4: Image Generation Service

---

## ⚠️ Обмеження та вимоги

- **OS**: Windows 10/11 (native, без WSL2)
- **Python**: 3.10+
- **GPU**: NVIDIA з CUDA 12.1 (опціонально, але рекомендовано)
- **RAM**: Мінімум 8GB (рекомендовано 16GB+)
- **VRAM**: Мінімум 6GB для Ollama моделей
- **Ollama**: Має бути встановлений та запущений

---

## 🛠️ Troubleshooting

### Ollama не відповідає
```bash
# Перевірка статусу
curl http://localhost:11434/api/tags

# Перезапуск Ollama (Windows)
taskkill /F /IM ollama.exe
ollama serve
```

### CUDA не знайдено
```bash
# Перевірка CUDA toolkit
nvcc --version

# Перевірка PyTorch CUDA
python -c "import torch; print(torch.version.cuda)"
```

### Помилка імпорту nvidia-ml-py
```bash
# Переустановка
pip uninstall nvidia-ml-py
pip install nvidia-ml-py==12.560.30
```

---

## 📝 Ліцензія

MIT License (або вкажи свою)

---

## 👤 Автор

Створено для локального AI асистента з фокусом на приватність та продуктивність.

**Версія**: 1.0.0 (Phase 1)  
**Дата**: 2026-04-30
