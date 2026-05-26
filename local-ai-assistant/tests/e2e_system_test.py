import requests
import time
import base64
import os

def test_full_cycle():
    print("=== STARTING FULL SYSTEM E2E TEST ===")
    
    # 1. Prepare for STT
    print("\n[1/4] Testing STT Preparation & Transcription...")
    prep_stt = requests.post("http://localhost:8004/prepare/stt").json()
    print(f"Orchestrator: {prep_stt['status']}, VRAM: {prep_stt['vram']['used_mb']}MB")
    
    # Check if test file exists
    audio_path = r"E:\projects\AI\local-ai-assistant\tests\test_audio_10s.wav"
    if os.path.exists(audio_path):
        with open(audio_path, "rb") as f:
            stt_resp = requests.post("http://localhost:8001/v1/audio/transcriptions", files={"file": f}).json()
        print(f"STT Result: '{stt_resp.get('text')}'")
    else:
        print("STT Skip: Test audio file not found.")

    # 2. Prepare for LLM
    print("\n[2/4] Testing LLM Preparation & Generation...")
    prep_llm = requests.post("http://localhost:8004/prepare/llm").json()
    print(f"Orchestrator: {prep_llm['status']}, VRAM: {prep_llm['vram']['used_mb']}MB")
    
    llm_payload = {
        "model": "qwen2.5:7b",
        "prompt": "Say 'System integrated' in Ukrainian.",
        "stream": False,
        "options": {"num_ctx": 2048, "num_gpu": 22}
    }
    llm_resp = requests.post("http://localhost:11434/api/generate", json=llm_payload).json()
    print(f"LLM Result: '{llm_resp.get('response')}'")

    # 3. Test TTS
    print("\n[3/4] Testing TTS (Piper)...")
    tts_payload = {"model": "tts-1", "input": "Система інтегрована", "voice": "uk"}
    tts_resp = requests.post("http://localhost:8002/v1/audio/speech", json=tts_payload)
    if tts_resp.status_code == 200:
        print(f"TTS Result: Success (Received {len(tts_resp.content)} bytes)")
    else:
        print(f"TTS Error: {tts_resp.text}")

    # 4. Prepare for Image Gen
    print("\n[4/4] Testing Image Gen Preparation & Generation...")
    prep_img = requests.post("http://localhost:8004/prepare/image").json()
    print(f"Orchestrator: {prep_img['status']}, VRAM: {prep_img['vram']['used_mb']}MB")
    
    img_payload = {"prompt": "a futuristic robot assistant, high quality", "steps": 2}
    img_resp = requests.post("http://localhost:8003/api/v1/generate", json=img_payload).json()
    if "image" in img_resp:
        print(f"Image Gen Result: Success (Received base64 string)")
    else:
        print(f"Image Gen Error: {img_resp}")

    print("\n=== E2E TEST COMPLETE ===")

if __name__ == "__main__":
    test_full_cycle()
