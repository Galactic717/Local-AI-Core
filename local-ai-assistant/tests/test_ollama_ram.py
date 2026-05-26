import requests
import json

def test_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen2.5:7b",
        "prompt": "Привіт, як справи?",
        "stream": False,
        "options": {
            "num_ctx": 4096,
            "num_gpu": 22
        }
    }
    
    print(f"Sending request to Ollama for {payload['model']}...")
    try:
        response = requests.post(url, json=payload, timeout=60)
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response:", response.json().get("response"))
        else:
            print("Error:", response.text)
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_ollama()
