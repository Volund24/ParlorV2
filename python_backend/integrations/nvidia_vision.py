import aiohttp
from config import settings

class NvidiaVision:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        # Using Llama 3.2 11B Vision Instruct
        self.api_url = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions"

    async def describe_avatar(self, image_url):
        if not self.api_key:
            return "a mysterious fighter"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "meta/llama-3.2-11b-vision-instruct",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Describe the character in this image in 1 sentence. Focus on visual traits like clothing, hair, and accessories."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": image_url
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 60,
            "temperature": 0.2,
            "top_p": 0.7,
            "stream": False
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        print(f"NVIDIA Vision API Error: {response.status}")
                        return "a mysterious fighter"
                    
                    data = await response.json()
                    description = data['choices'][0]['message']['content']
                    # Clean up the description
                    return description.replace("The character is ", "").replace("The image shows ", "").strip()
            except Exception as e:
                print(f"NVIDIA Vision Exception: {e}")
                return "a mysterious fighter"
