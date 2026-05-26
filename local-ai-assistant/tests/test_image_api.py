import requests
import base64
import os
import time

url = "http://localhost:8003/v1/images/generations"
payload = {
    "prompt": "a futuristic cybernetic cat in a neon city, highly detailed, 4k",
    "width": 512,
    "height": 512,
    "num_inference_steps": 1,
    "guidance_scale": 0.0
}

print(f"Sending request to {url}...")
print("Note: This will trigger VRAM unload and load SD Turbo. It might take a moment...")

start_time = time.time()
try:
    response = requests.post(url, json=payload, timeout=120)

    if response.status_code == 200:
        elapsed = time.time() - start_time
        print(f"Success! Generation took {elapsed:.2f}s")
        
        data = response.json()
        img_b64 = data['data'][0]['b64_json']
        
        output_path = "E:/projects/AI/local-ai-assistant/temp/test_image.png"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, "wb") as f:
            f.write(base64.b64decode(img_b64))
            
        print(f"Saved image to {output_path}")
    else:
        print(f"Error {response.status_code}: {response.text}")
except Exception as e:
    print(f"Request failed: {e}")
