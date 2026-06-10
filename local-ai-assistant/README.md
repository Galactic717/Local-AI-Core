# Local AI Assistant: Modular Multi-Model Router

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Modern_Web_Framework-009688.svg)](https://fastapi.tiangolo.com/)

**Local AI Assistant** — це універсальна платформа для роботи з локальними мовними моделями, яка фокусується на розумній маршрутизації запитів та інтеграції з персональними базами знань (Obsidian).

## 🌟 Основні можливості

*   **Brain Router:** Інтелектуальна система, що обирає найкращу модель для кожного запиту (напр. кодування -> Llama 3, креатив -> Gemma).
*   **Obsidian Integration:** Прямий доступ до ваших заміток для створення персонального контексту.
*   **Multi-Model Support:** Одночасна робота з Ollama, LM Studio та іншими провайдерами.
*   **VRAM Management:** Автоматичний моніторинг ресурсів відеокарти для стабільної роботи локальних моделей.
*   **Extensible Architecture:** Легке додавання нових модулів (Shell Executor, Python Runner).

## 🛠 Технологічний стек

*   **Core:** Python, FastAPI
*   **AI Routing:** Custom Logic + Semantic Analysis
*   **Data:** Obsidian API, Local File System
*   **Frontend:** Electron Desktop UI

## 🚀 Як почати

1.  Встановіть залежності: `pip install -r requirements.txt`
2.  Налаштуйте шляхи до вашого Obsidian Vault у `.env`.
3.  Запустіть асистента: `python run_local_ai.bat`

---
*Проект фокусується на створенні повністю приватного та автономного робочого середовища для розробника.*
