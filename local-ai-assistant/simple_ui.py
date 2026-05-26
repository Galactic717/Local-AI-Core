"""
Simple Web UI for Local AI Assistant
Lightweight alternative to Open WebUI
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
import json
from typing import Optional
from brain_router import BrainRouter

app = FastAPI(title="Local AI Assistant UI")
brain_router = BrainRouter()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service endpoints
OLLAMA_URL = "http://localhost:11434"
STT_URL = "http://localhost:8001"
TTS_URL = "http://localhost:8002"
IMAGE_URL = "http://localhost:8003"
ORCHESTRATOR_URL = "http://localhost:8004"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Local AI Assistant</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 800px;
            height: 90vh;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 {
            font-size: 24px;
            margin-bottom: 5px;
        }
        .status {
            font-size: 12px;
            opacity: 0.9;
        }
        .chat-container {
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            align-items: flex-start;
        }
        .message.user {
            justify-content: flex-end;
        }
        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 18px;
            word-wrap: break-word;
        }
        .message.user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }
        .message.assistant .message-content {
            background: white;
            color: #333;
            border-bottom-left-radius: 4px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .input-container {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }
        #input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.3s;
        }
        #input:focus {
            border-color: #667eea;
        }
        button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 600;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        button:active {
            transform: translateY(0);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        .loading {
            display: none;
            text-align: center;
            padding: 10px;
            color: #666;
        }
        .loading.active {
            display: block;
        }
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 12px 16px;
        }
        .typing-indicator span {
            width: 8px;
            height: 8px;
            background: #999;
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }
        .typing-indicator span:nth-child(2) {
            animation-delay: 0.2s;
        }
        .typing-indicator span:nth-child(3) {
            animation-delay: 0.4s;
        }
        @keyframes typing {
            0%, 60%, 100% {
                transform: translateY(0);
            }
            30% {
                transform: translateY(-10px);
            }
        }
        .error {
            background: #ff4444;
            color: white;
            padding: 10px;
            border-radius: 8px;
            margin: 10px 20px;
            text-align: center;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Local AI Assistant</h1>
            <div class="status" id="status">Підключення...</div>
        </div>
        <div class="chat-container" id="chat">
            <div class="message assistant">
                <div class="message-content">
                    Привіт! Я Local AI Assistant. Можу допомогти з текстом, генерацією зображень та голосовим спілкуванням. Що вас цікавить?
                </div>
            </div>
        </div>
        <div class="loading" id="loading">
            <div class="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
        <div class="input-container">
            <input
                type="text"
                id="input"
                placeholder="Введіть повідомлення..."
                onkeypress="if(event.key==='Enter') send()"
            />
            <button onclick="send()" id="sendBtn">Надіслати</button>
        </div>
    </div>

    <script>
        const chat = document.getElementById('chat');
        const input = document.getElementById('input');
        const loading = document.getElementById('loading');
        const sendBtn = document.getElementById('sendBtn');
        const status = document.getElementById('status');

        // Check services status
        async function checkStatus() {
            try {
                const response = await fetch('http://localhost:8004/status');
                if (response.ok) {
                    status.textContent = '✅ Всі сервіси працюють';
                } else {
                    status.textContent = '⚠️ Деякі сервіси недоступні';
                }
            } catch (error) {
                status.textContent = '❌ Помилка підключення';
            }
        }

        checkStatus();
        setInterval(checkStatus, 30000); // Check every 30s

        function addMessage(text, isUser) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'assistant'}`;

            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = text;

            messageDiv.appendChild(contentDiv);
            chat.appendChild(messageDiv);
            chat.scrollTop = chat.scrollHeight;
        }

        function showError(message) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = message;
            chat.appendChild(errorDiv);
            setTimeout(() => errorDiv.remove(), 5000);
        }

        async function send() {
            const message = input.value.trim();
            if (!message) return;

            // Add user message
            addMessage(message, true);
            input.value = '';

            // Show loading
            loading.classList.add('active');
            sendBtn.disabled = true;

            try {
                // First, get model recommendation from brain router
                const routerResponse = await fetch('/api/select-model', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        query: message
                    })
                });

                const routerData = await routerResponse.json();
                const selectedModel = routerData.model;

                console.log('Brain Router selected:', selectedModel);
                console.log('Reasons:', routerData.reasons);

                // Send to Ollama with selected model
                const response = await fetch('http://localhost:11434/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        model: selectedModel,
                        prompt: message,
                        stream: false
                    })
                });

                if (!response.ok) {
                    throw new Error('Ollama не відповідає');
                }

                const data = await response.json();

                // Add AI response with model info
                const responseText = data.response + '\n\n[Model: ' + selectedModel + ']';
                addMessage(responseText, false);

            } catch (error) {
                console.error('Error:', error);
                showError('❌ Помилка: ' + error.message);
            } finally {
                loading.classList.remove('active');
                sendBtn.disabled = false;
                input.focus();
            }
        }

        // Focus input on load
        input.focus();
    </script>
</body>
</html>
"""

@app.get("/")
async def get_ui():
    """Serve the web UI"""
    return HTMLResponse(HTML_TEMPLATE)

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "service": "Simple UI"}

@app.get("/api/status")
async def get_status():
    """Get status of all services"""
    services = {}

    async with httpx.AsyncClient(timeout=2.0) as client:
        # Check Orchestrator
        try:
            resp = await client.get(f"{ORCHESTRATOR_URL}/status")
            services["orchestrator"] = "ok" if resp.status_code == 200 else "error"
        except:
            services["orchestrator"] = "offline"

        # Check STT
        try:
            resp = await client.get(f"{STT_URL}/health")
            services["stt"] = "ok" if resp.status_code == 200 else "error"
        except:
            services["stt"] = "offline"

        # Check TTS
        try:
            resp = await client.get(f"{TTS_URL}/health")
            services["tts"] = "ok" if resp.status_code == 200 else "error"
        except:
            services["tts"] = "offline"

        # Check Image
        try:
            resp = await client.get(f"{IMAGE_URL}/health")
            services["image"] = "ok" if resp.status_code == 200 else "error"
        except:
            services["image"] = "offline"

        # Check Ollama
        try:
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            services["ollama"] = "ok" if resp.status_code == 200 else "error"
        except:
            services["ollama"] = "offline"

    return services

@app.post("/api/select-model")
async def select_model(request: dict):
    """Select best model using brain router"""
    query = request.get("query", "")

    # Use brain router to select model
    result = brain_router.select_model(query, available_ram_gb=12.0)

    return {
        "model": result["model"],
        "score": result["score"],
        "reasons": result["reasons"],
        "description": result.get("description", ""),
        "query_analysis": result["query_analysis"]
    }

if __name__ == "__main__":
    import uvicorn
    print("Starting Simple UI with Brain Router on http://localhost:8081")
    print("Services:")
    print(f"   - Ollama: {OLLAMA_URL}")
    print(f"   - STT: {STT_URL}")
    print(f"   - TTS: {TTS_URL}")
    print(f"   - Image: {IMAGE_URL}")
    print(f"   - Orchestrator: {ORCHESTRATOR_URL}")
    uvicorn.run(app, host="0.0.0.0", port=8081)
