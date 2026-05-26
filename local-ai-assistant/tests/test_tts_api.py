import requests
import os

url = "http://localhost:8002/v1/audio/speech"
payload = {
    "input": "Привіт, я твій локальний асистент.",
    "voice": "uk"
}

print(f"Sending request to {url}...")
response = requests.post(url, json=payload)

if response.status_code == 200:
    output_path = "E:/projects/AI/local-ai-assistant/temp/test_tts_python.wav"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(response.content)
    print(f"Success! Saved to {output_path}")
    print(f"File size: {os.path.getsize(output_path)} bytes")
else:
    print(f"Error {response.status_code}: {response.text}")
