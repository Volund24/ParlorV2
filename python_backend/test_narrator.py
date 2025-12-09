import asyncio
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv("python_backend/.env")
api_key = os.getenv("NVIDIA_API_KEY")

async def test_narrator():
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "meta/llama-3.1-405b-instruct",
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 10
    }
    
    print(f"Testing Narrator URL: {url}")
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            print(f"Status: {response.status}")
            print(await response.text())

if __name__ == "__main__":
    asyncio.run(test_narrator())
