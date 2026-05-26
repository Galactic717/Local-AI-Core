# ============================================
# LOCAL AI ASSISTANT - Phase 1 Setup Guide
# ============================================

## ✅ Створені файли

### 📁 Структура проекту
```
E:\projects\AI\local-ai-assistant\
├── config/
│   ├── ollama_config.yaml      ✅ (v1.2 patch, VRAM 5200 MB)
│   ├── stt_config.yaml          ✅ (Faster-Whisper base int8)
│   ├── tts_config.yaml          ✅ (Piper uk_UA CPU mode)
│   └── image_gen_config.yaml   ✅ (SD Turbo fp16)
├── services/
│   └── orchestrator.py          ✅ (Threading.Lock, verify /api/ps)
├── scripts/
│   ├── start_services.bat       ✅ (Запуск orchestrator)
│   ├── stop_services.bat        ✅ (Зупинка через WINDOWTITLE)
│   ├── monitor_vram.py          ✅ (Real-time dashboard)
│   ├── health_check.py          ✅ (Перевірка портів)
│   └── check_installation.bat   ✅ (Перевірка середовища)
├── .env.example                 ✅ (Dynamic paths, VRAM 5200)
├── requirements.txt             ✅ (Phase 1 залежності)
└── README.md                    ✅ (Інструкції)
```

---

## 🚀 Швидкий старт

### 1️⃣ Створення віртуального середовища

```bash
cd E:\projects\AI\local-ai-assistant

# Створення venv
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

# PyTorch з CUDA 12.1 (якщо є NVIDIA GPU)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

### 3️⃣ Налаштування середовища

```bash
# Копіювання .env
copy .env.example .env

# Редагування (опціонально)
notepad .env
```

### 4️⃣ Перевірка встановлення

```bash
# Автоматична перевірка
scripts\check_installation.bat

# Або вручну:
python --version          # 3.10+
nvcc --version            # CUDA toolkit
nvidia-smi                # GPU info
curl http://localhost:11434/api/tags  # Ollama
```

---

## 🎯 Запуск Phase 1

### Запуск Orchestrator

```bash
# Варіант 1: Через скрипт (рекомендовано)
scripts\start_services.bat

# Варіант 2: Вручну
cd E:\projects\AI\local-ai-assistant
venv\Scripts\activate
python services\orchestrator.py
```

### Перевірка статусу

```bash
# Health check
python scripts\health_check.py

# Або через curl
curl http://localhost:8004/health
curl http://localhost:8004/status
```

### Моніторинг VRAM

```bash
# Real-time dashboard
python scripts\monitor_vram.py
```

### Зупинка сервісів

```bash
scripts\stop_services.bat
```

---

## 🧪 Тестування

### 1. Перевірка VRAM моніторингу

```bash
# В окремому терміналі
python scripts\monitor_vram.py

# В іншому терміналі
curl http://localhost:8004/status
```

**Очікуваний результат:**
```json
{
  "used_mb": 500,
  "free_mb": 5644,
  "total_mb": 6144,
  "percent": 8.14,
  "threshold_mb": 5200,
  "status": "ok",
  "loaded_models": []
}
```

### 2. Тест підготовки для LLM

```bash
curl -X POST http://localhost:8004/prepare/llm \
  -H "Content-Type: application/json" \
  -d "{\"model_name\": \"qwen2.5:7b\", \"required_mb\": 3500}"
```

**Очікуваний результат:**
```json
{
  "status": "ready",
  "vram": {
    "used_mb": 500,
    "free_mb": 5644,
    "available": true
  }
}
```

### 3. Тест emergency unload

```bash
curl -X POST http://localhost:8004/unload/all
```

**Очікуваний результат:**
```json
{
  "status": "unloaded",
  "vram": {
    "used_mb": 300,
    "loaded_models": []
  }
}
```

---

## 📊 API Endpoints

### GET /status
Отримати поточний статус VRAM

```bash
curl http://localhost:8004/status
```

### GET /health
Health check

```bash
curl http://localhost:8004/health
```

### POST /prepare/llm
Підготувати VRAM для LLM

```bash
curl -X POST http://localhost:8004/prepare/llm \
  -H "Content-Type: application/json" \
  -d '{"model_name": "qwen2.5:7b", "required_mb": 3500}'
```

### POST /prepare/stt
Підготувати VRAM для STT

```bash
curl -X POST http://localhost:8004/prepare/stt
```

### POST /prepare/image
Підготувати VRAM для Image Gen

```bash
curl -X POST http://localhost:8004/prepare/image
```

### POST /unload/all
Emergency unload всіх моделей

```bash
curl -X POST http://localhost:8004/unload/all
```

---

## ⚠️ Troubleshooting

### Orchestrator не запускається

```bash
# Перевірка порту
netstat -ano | findstr :8004

# Якщо зайнятий
taskkill /F /PID <pid>
```

### VRAM не звільняється

```bash
# Emergency unload
curl -X POST http://localhost:8004/unload/all

# Або вручну
curl -X POST http://localhost:11434/api/generate -d "{\"model\":\"*\",\"keep_alive\":0}"
```

### Ollama не відповідає

```bash
# Перезапуск Ollama
taskkill /F /IM ollama.exe
ollama serve
```

### CUDA не знайдено

```bash
# Перевірка CUDA
nvcc --version
python -c "import torch; print(torch.cuda.is_available())"

# Переустановка PyTorch
pip uninstall torch torchvision torchaudio
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

---

## 📝 Ключові зміни v1.2

- ✅ VRAM threshold знижено з 5500 до **5200 MB**
- ✅ `qwen2.5:7b`: num_gpu_layers 22 (було 25)
- ✅ `deepseek-r1:8b`: num_gpu_layers 18 (було 20)
- ✅ `keep_alive` знижено до 10s (було 30s)
- ✅ `num_batch` знижено до 256 (було 512)
- ✅ `num_thread` знижено до 8 (було 14)
- ✅ `cooldown_sec` збільшено до 3 (було 2)
- ✅ Додано `threading.Lock` для race condition
- ✅ Додано `verify_ollama_unloaded()` через `/api/ps`
- ✅ Додано `aggressive_cleanup()` (torch + gc)

---

## 🎯 Definition of Done (Phase 1)

- [x] Структура проекту створена
- [x] Конфіги створені (v1.2 patch)
- [x] Orchestrator створений (threading.Lock, verify)
- [x] Скрипти запуску/зупинки створені
- [x] Моніторинг VRAM створений
- [x] Health check створений
- [ ] Virtual environment встановлений
- [ ] Залежності встановлені
- [ ] Orchestrator запущений та протестований
- [ ] VRAM моніторинг працює
- [ ] API endpoints протестовані

---

## 📚 Наступні кроки

### Phase 2: STT Integration
- Створити `services/stt_service.py`
- Інтегрувати Faster-Whisper
- Тестування voice input

### Phase 3: TTS Integration
- Створити `services/tts_service.py`
- Інтегрувати Piper TTS
- Тестування voice output

### Phase 4: Image Generation
- Створити `services/image_gen_service.py`
- Інтегрувати SD Turbo
- Тестування image generation

---

**Версія:** 1.2  
**Дата:** 2026-04-30  
**Статус:** Phase 1 Ready to Test
