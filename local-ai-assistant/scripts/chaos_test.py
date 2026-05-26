
import requests
import threading
import time
import uuid
import os
import json
from pathlib import Path

# Configuration
STT_URL = "http://localhost:8001/v1/audio/transcriptions"
TTS_URL = "http://localhost:8002/v1/audio/speech"
IMG_URL = "http://localhost:8003/api/v1/generate"
LLM_URL = "http://localhost:11434/api/generate"
ORCH_URL = "http://localhost:8004/status"

RESULTS_FILE = "logs/stress_test_results.json"
VRAM_LOG = "logs/stress_vram_monitor.log"

def log_vram():
    """Monitor VRAM every second in a background thread"""
    with open(VRAM_LOG, "w") as f:
        f.write("timestamp,used_mb,free_mb\n")
        while not stop_test:
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                used = info.used // (1024**2)
                free = info.free // (1024**2)
                f.write(f"{time.time()},{used},{free}\n")
                f.flush()
            except:
                pass
            time.sleep(1)

def run_stt():
    print("[QA] Starting STT request...")
    try:
        files = {'file': open('tests/test_audio_10s.wav', 'rb')}
        r = requests.post(STT_URL, files=files, data={'language': 'en'}, timeout=30)
        print(f"[QA] STT Response: {r.status_code}")
    except Exception as e: print(f"[QA] STT Error: {e}")

def run_tts():
    print("[QA] Starting TTS request...")
    try:
        r = requests.post(TTS_URL, json={'input': 'This is a stress test of the multimodal system.', 'voice': 'en'}, timeout=30)
        print(f"[QA] TTS Response: {r.status_code}")
    except Exception as e: print(f"[QA] TTS Error: {e}")

def run_image(prompt):
    print(f"[QA] Starting Image request: {prompt}...")
    try:
        r = requests.post(IMG_URL, json={'prompt': prompt, 'steps': 2}, timeout=60)
        print(f"[QA] Image Response: {r.status_code}")
    except Exception as e: print(f"[QA] Image Error: {e}")

def run_llm():
    print("[QA] Starting LLM request...")
    try:
        r = requests.post(LLM_URL, json={'model': 'phi4-mini', 'prompt': 'Explain quantum physics in 2 sentences.', 'stream': False}, timeout=60)
        print(f"[QA] LLM Response: {r.status_code}")
    except Exception as e: print(f"[QA] LLM Error: {e}")

# MAIN EXECUTION
stop_test = False
print("="*60)
print("🚀 STARTING MULTIMODAL CHAOS TEST (v1.4)")
print("="*60)

vram_thread = threading.Thread(target=log_vram, daemon=True)
vram_thread.start()

try:
    # Phase 1: Heavy concurrent load (STT + LLM + TTS)
    print("\n--- PHASE 1: Concurrent Load ---")
    t1 = threading.Thread(target=run_stt)
    t2 = threading.Thread(target=run_llm)
    t3 = threading.Thread(target=run_tts)
    
    t1.start(); t2.start(); t3.start()
    time.sleep(10) # Let them run
    
    # Phase 2: The Swap (Trigger Image Gen while others might still be finishing)
    print("\n--- PHASE 2: The VRAM Swap ---")
    run_image("a chaotic digital explosion of colors")
    
    # Phase 3: Rapid Fire
    print("\n--- PHASE 3: Rapid Fire Images ---")
    for i in range(2):
        run_image(f"stress test image number {i}")
        time.sleep(2)
        
    # Phase 4: Recovery and LLM Reload
    print("\n--- PHASE 4: Recovery ---")
    time.sleep(10)
    run_llm() # Test if LLM can reload after Image Gen purge
    
    print("\n--- FINISHED ---")

finally:
    stop_test = True
    vram_thread.join(timeout=2)
    print("="*60)
    print("✅ TEST SEQUENCE COMPLETED")
    print("="*60)
