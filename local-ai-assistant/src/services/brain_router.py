"""
Brain Router - direct chat routing plus agent mode with local tools.
"""

import re
import sys
from pathlib import Path
from typing import List

import requests
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.agent import run_agent_session
from src.utils.config_loader import get_service_url, load_services_config
from src.utils.logger import setup_logger
from src.utils.runtime_paths import ensure_writable_dir

logger = setup_logger("brain_router", ensure_writable_dir("logs") / "router.log")

app = FastAPI(title="Codex Brain Router", version="1.7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ORCHESTRATOR_URL = get_service_url("orchestrator")
OLLAMA_URL = get_service_url("ollama")
IMAGE_SERVICE_URL = f"{get_service_url('image_gen')}/api/v1/generate"

_svc_cfg = load_services_config()
MODEL_REQUIREMENTS_MB = _svc_cfg.get(
    "model_requirements_mb",
    {
        "phi4-mini:latest": 2500,
        "qwen2.5:7b": 4200,
        "deepseek-r1:8b": 4600,
        "aya-expanse:8b": 5100,
        "llama3.2:latest": 2000,
        "gemma4:e4b": 5600,
    },
)

MODEL_FAST = "phi4-mini:latest"
MODEL_DEFAULT = "llama3.2:latest"
MODEL_UKRAINIAN = "aya-expanse:8b"
MODEL_MATH = "qwen2.5:7b"
MODEL_REASONING = "deepseek-r1:8b"
MODEL_VISION = "gemma4:e4b"

ROUTER_TIMEOUT_SEC = 120
GENERATION_TIMEOUT_SEC = 300


class ChatRequest(BaseModel):
    messages: List[dict]
    stream: bool = False


class AgentChatRequest(BaseModel):
    messages: List[dict]
    stream: bool = False


def detect_intent(message: dict) -> str:
    """
    Rule-based intent detection for the local model stack.
    """
    if message.get("images") and len(message["images"]) > 0:
        return MODEL_VISION

    text = str(message.get("content", "")).strip().lower()

    if text.startswith("/image"):
        return "image_gen"

    image_keywords = [
        "generate image",
        "draw",
        "photo",
        "picture",
        "image",
        "намалюй",
        "зображення",
        "картинка",
        "створи фото",
    ]
    if any(word in text for word in image_keywords):
        return "image_gen"

    math_keywords = ["рахуй", "math", "solve", "обчисли", "scientific", "калькул", "формула"]
    if any(word in text for word in math_keywords):
        return MODEL_MATH

    reasoning_keywords = ["подумай", "think", "чому", "why", "reason", "логіч", "аналіз"]
    if any(word in text for word in reasoning_keywords):
        return MODEL_REASONING

    fast_keywords = [
        "mcp",
        "tool",
        "obsidian",
        "search",
        "прочитай",
        "відкрий файл",
        "створи файл",
        "запиши",
        "список файлів",
        "директорі",
        "папк",
        "переглянь",
        "code",
        "coding",
        "bug",
        "fix",
        "refactor",
        "python",
        "javascript",
        "typescript",
        "react",
        "fastapi",
        "shell",
        "terminal",
        "command",
        "file",
        "files",
        "repo",
        "repository",
        "код",
        "проєкт",
        "проект",
        "файл",
        "файли",
        "помил",
        "команд",
        "термінал",
        "консоль",
        "скрипт",
    ]
    if any(word in text for word in fast_keywords):
        return MODEL_MATH

    uk_indicators = [
        "привіт",
        "як справи",
        "розкажи",
        "поясни",
        "допоможи",
        "українська",
        "переклади",
        "напиши",
        "що ти вмієш",
        "розмовля",
        "укр",
    ]
    if any(word in text for word in uk_indicators):
        return MODEL_UKRAINIAN

    return MODEL_DEFAULT


def normalize_image_prompt(text: str) -> str:
    if text.lower().startswith("/image"):
        normalized = text[6:].strip()
        return normalized or "Concept art of a local AI assistant workspace"
    return text


def enhance_image_prompt_if_needed(prompt: str) -> str:
    try:
        logger.info("Enhancing prompt using LLM: %s", prompt)
        required_mb = MODEL_REQUIREMENTS_MB.get(MODEL_UKRAINIAN, 5100)
        requests.post(
            f"{ORCHESTRATOR_URL}/prepare/llm",
            json={"model_name": MODEL_UKRAINIAN, "required_mb": required_mb},
            timeout=ROUTER_TIMEOUT_SEC,
        ).raise_for_status()

        system_prompt = (
            "You are an expert prompt engineer for Stable Diffusion. "
            "Take the user's input (in any language) and translate/expand it into a highly detailed, "
            "masterpiece-quality English prompt. Include lighting, camera angles, artistic style, and atmosphere. "
            "Output ONLY the English prompt. Do not include quotes, greetings, or explanations."
        )

        payload = {
            "model": MODEL_UKRAINIAN,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            "options": {"num_predict": 150, "temperature": 0.4}
        }
        resp = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=payload,
            timeout=GENERATION_TIMEOUT_SEC,
        )
        resp.raise_for_status()
        english_prompt = resp.json()["message"]["content"].strip()
        logger.info("Enhanced prompt: %s", english_prompt)
        return english_prompt
    except Exception as e:
        logger.error("Failed to enhance prompt: %s", e)
        return prompt


def generate_image_response(prompt_text: str) -> dict:
    image_prompt = normalize_image_prompt(prompt_text)
    enhanced_prompt = enhance_image_prompt_if_needed(image_prompt)
    resp = requests.post(
        IMAGE_SERVICE_URL,
        json={"prompt": enhanced_prompt},
        timeout=GENERATION_TIMEOUT_SEC,
    )
    resp.raise_for_status()
    payload = resp.json()
    return {
        "model": "sd_turbo",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Ось згенероване зображення.",
                }
            }
        ],
        "events": [],
        "image_b64": payload.get("image"),
    }


import asyncio

@app.post("/api/v1/chat")
async def chat_router(request: ChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    last_msg_dict = request.messages[-1]
    last_msg_content = last_msg_dict.get("content", "")
    intent = detect_intent(last_msg_dict)

    logger.info("Detected intent: %s for message: %s...", intent, str(last_msg_content)[:50])

    if intent == "image_gen":
        try:
            return await asyncio.to_thread(generate_image_response, last_msg_content)
        except requests.exceptions.Timeout as exc:            raise HTTPException(
                status_code=504,
                detail="Image generation service timed out (60s)",
            ) from exc
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Image generation request failed: {exc}",
            ) from exc

    try:
        required_mb = MODEL_REQUIREMENTS_MB.get(intent, 3500)
        prepare_response = requests.post(
            f"{ORCHESTRATOR_URL}/prepare/llm",
            json={"model_name": intent, "required_mb": required_mb},
            timeout=ROUTER_TIMEOUT_SEC,
        )
        prepare_response.raise_for_status()

        ollama_payload = {
            "model": intent,
            "messages": request.messages,
            "stream": request.stream,
            "options": {"num_ctx": 4096},
        }

        response = requests.post(
            f"{OLLAMA_URL}/api/chat",
            json=ollama_payload,
            timeout=GENERATION_TIMEOUT_SEC,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout as exc:
        logger.error("Router timeout: %s", exc)
        raise HTTPException(status_code=504, detail="LLM request timed out") from exc
    except requests.RequestException as exc:
        logger.error("Router transport error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Router error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/api/v2/agent/chat")
async def agent_chat(request: AgentChatRequest):
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    last_msg_dict = request.messages[-1]
    last_msg_content = last_msg_dict.get("content", "")
    intent = detect_intent(last_msg_dict)

    logger.info("Agent intent: %s for message: %s...", intent, str(last_msg_content)[:50])

    if intent == "image_gen":
        try:
            return await asyncio.to_thread(generate_image_response, last_msg_content)
        except requests.exceptions.Timeout as exc:
            raise HTTPException(
                status_code=504,
                detail="Image generation service timed out (60s)",
            ) from exc
        except requests.RequestException as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Image generation request failed: {exc}",
            ) from exc

    if intent == MODEL_VISION:
        try:
            required_mb = MODEL_REQUIREMENTS_MB.get(intent, 5600)
            def _prepare_and_call():
                requests.post(
                    f"{ORCHESTRATOR_URL}/prepare/llm",
                    json={"model_name": intent, "required_mb": required_mb},
                    timeout=ROUTER_TIMEOUT_SEC,
                ).raise_for_status()

                # Force the vision model to respond in Ukrainian
                vision_messages = [dict(m) for m in request.messages]
                if vision_messages:
                    last_msg = dict(vision_messages[-1])
                    last_msg["content"] = str(last_msg.get("content", "")) + "\n\nIMPORTANT INSTRUCTION: You are an expert AI assistant. You MUST provide your entire analysis and response exclusively in the Ukrainian language (Українською мовою). Do not answer in English."
                    vision_messages[-1] = last_msg

                response = requests.post(
                    f"{OLLAMA_URL}/api/chat",
                    json={
                        "model": intent,
                        "messages": vision_messages,
                        "stream": request.stream,
                    },
                    timeout=GENERATION_TIMEOUT_SEC,
                )
                response.raise_for_status()
                return response.json()
            
            return await asyncio.to_thread(_prepare_and_call)
        except Exception as exc:
            logger.error("Vision request failed: %s", exc)
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    selected_model = intent if intent in MODEL_REQUIREMENTS_MB else MODEL_DEFAULT

    try:
        agent_result = await asyncio.to_thread(run_agent_session, request.messages, selected_model)
        return {
            "model": agent_result.model,
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": agent_result.response,
                    }
                }
            ],
            "events": agent_result.events,
        }
    except requests.exceptions.Timeout as exc:
        logger.error("Agent timeout: %s", exc)
        raise HTTPException(status_code=504, detail="Agent request timed out") from exc
    except requests.RequestException as exc:
        logger.error("Agent transport error: %s", exc)
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    except Exception as exc:
        logger.error("Agent error: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "ok", "service": "Brain Router"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
