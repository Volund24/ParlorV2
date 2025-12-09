import asyncio
import aiohttp
import os
import base64
from dotenv import load_dotenv

load_dotenv("python_backend/.env")
api_key = os.getenv("NVIDIA_API_KEY")

async def test_endpoints():
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        # 1. Test Narrator (Llama 3.1 405B)
        print("\n--- Testing Narrator ---")
        # Try the integrate endpoint
        url_text = "https://integrate.api.nvidia.com/v1/chat/completions"
        payload_text = {
            "model": "meta/llama-3.1-405b-instruct",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10,
            "temperature": 0.7,
            "top_p": 1
        }
        try:
            async with session.post(url_text, headers=headers, json=payload_text) as resp:
                print(f"URL: {url_text}")
                print(f"Status: {resp.status}")
                if resp.status != 200:
                    print(f"Error: {await resp.text()}")
                else:
                    print("Success!")
                    print(await resp.json())
        except Exception as e:
            print(f"Exception: {e}")

        # 2. Test Vision (Llama 3.2 11B Vision)
        print("\n--- Testing Vision ---")
        # Try integrate endpoint for vision too
        url_vision = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions" 
        payload_vision = {
            "model": "meta/llama-3.2-11b-vision-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe image"},
                        {"type": "image_url", "image_url": {"url": "https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png"}}
                    ]
                }
            ],
            "max_tokens": 10,
            "stream": False
        }
        try:
            async with session.post(url_vision, headers=headers, json=payload_vision) as resp:
                print(f"URL: {url_vision}")
                print(f"Status: {resp.status}")
                if resp.status != 200:
                    print(f"Error: {await resp.text()}")
                else:
                    print("Success!")
                    print(await resp.json())
        except Exception as e:
            print(f"Exception: {e}")

        # 3. Test Image (Flux.1)
        print("\n--- Testing Image ---")
        url_image = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"
        payload_image = {
            "prompt": "A simple cube",
            "steps": 4,
            "seed": 0
        }
        try:
            async with session.post(url_image, headers=headers, json=payload_image) as resp:
                print(f"URL: {url_image}")
                print(f"Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json()
                    if 'artifacts' in data:
                        b64 = data['artifacts'][0]['base64']
                        print(f"Image Size: {len(b64)} chars")
                        with open("debug_image.jpg", "wb") as f:
                            f.write(base64.b64decode(b64))
                        print("Saved debug_image.jpg")
                    else:
                        print(f"No artifacts: {data.keys()}")
                else:
                    print(f"Error: {await resp.text()}")
        except Exception as e:
            print(f"Exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_endpoints())
