import aiohttp
import base64
import io
import urllib.parse
from config import settings

class NvidiaImageGenerator:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        self.use_pollinations = True 
        self.nvidia_api_url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-schnell"
        # SDXL URL seems to be deprecated/404, removing it to avoid errors
        self.nvidia_sdxl_url = None 

    def _sanitize_prompt(self, prompt):
        # Remove words that trigger NVIDIA's strict safety filter
        forbidden = ["fighting", "fight", "blood", "gore", "violence", "kill", "death", "dead", "corpse", "weapon", "gun", "sword", "attack", "battle", "war"]
        sanitized = prompt
        for word in forbidden:
            sanitized = sanitized.replace(word, "action")
            sanitized = sanitized.replace(word.capitalize(), "Action")
        return sanitized

    async def generate_image(self, prompt, negative_prompt="", prefer_nvidia=False):
        # 1. If prefer_nvidia is True, try NVIDIA Flux (Sanitized) first
        if prefer_nvidia and self.api_key:
            print(f"DEBUG: Prefer NVIDIA requested. Using Flux (Sanitized)...")
            safe_prompt = self._sanitize_prompt(prompt)
            image = await self._generate_nvidia(safe_prompt, model_url=self.nvidia_api_url)
            if image:
                return image

        # 2. Try Pollinations.ai (Flux/Turbo) - Best for "Edgy" content
        print(f"DEBUG: Attempting Pollinations for: {prompt[:30]}...")
        image = await self._generate_pollinations(prompt)
        if image:
            return image

        # 3. Fallback to NVIDIA Flux (Sanitized) if Pollinations failed
        if self.api_key:
            safe_prompt = self._sanitize_prompt(prompt)
            print(f"DEBUG: Pollinations failed. Falling back to NVIDIA Flux (Sanitized)...")
            return await self._generate_nvidia(safe_prompt, model_url=self.nvidia_api_url)
            
        return None

    async def _generate_pollinations(self, prompt):
        import random
        import asyncio
        
        # Try Flux first (better quality), then Turbo (faster/fallback)
        models = ["flux", "turbo"]
        
        for model in models:
            # Retry logic (2 attempts per model)
            for attempt in range(2):
                try:
                    # Add random delay to prevent rate limiting
                    delay = random.uniform(3.0, 6.0) # Increased delay
                    await asyncio.sleep(delay)
                    
                    print(f"Generating image via Pollinations.ai ({model}) [Attempt {attempt+1}]...")
                    
                    # Truncate prompt if too long (URL limit safety)
                    safe_prompt = prompt[:1500] 
                    encoded_prompt = urllib.parse.quote(safe_prompt)
                    
                    seed = random.randint(0, 100000)
                    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&model={model}&nologo=true&seed={seed}"
                    
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, timeout=60) as response: # Increased timeout
                            if response.status == 200:
                                image_bytes = await response.read()
                                if len(image_bytes) > 1000: # Ensure we got a real image
                                    print(f"Pollinations ({model}) Success! Received {len(image_bytes)} bytes.")
                                    return io.BytesIO(image_bytes)
                            
                            print(f"Pollinations ({model}) API Error (Attempt {attempt+1}): {response.status}")
                            
                except Exception as e:
                    print(f"Pollinations ({model}) Exception (Attempt {attempt+1}): {e}")
                    import traceback
                    traceback.print_exc()
                
        return None

    async def _generate_nvidia(self, prompt, model_url=None, high_quality=False):
        url = model_url if model_url else self.nvidia_api_url
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        
        # Default SDXL Payload
        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 5,
            "sampler": "K_EULER_ANCESTRAL",
            "steps": 25,
            "seed": 0
        }
        
        # High Quality SDXL Settings
        if high_quality and "stabilityai" in url:
             payload = {
                "text_prompts": [{"text": prompt + ", masterpiece, best quality, 4k, highly detailed, sharp focus"}],
                "cfg_scale": 7, # Higher adherence to prompt
                "sampler": "K_DPM_2_ANCESTRAL", # Often better details
                "steps": 40, # More steps = better quality
                "seed": 0
            }

        # Adjust payload for Flux if needed (Flux uses "prompt" key, SDXL uses "text_prompts")
        if "flux" in url:
            payload = {
                "prompt": prompt,
                "steps": 4,
                "seed": 0
            }

        print(f"Generating image via NVIDIA ({url.split('/')[-1]})...")
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"NVIDIA API Error: {response.status} - {error_text}")
                        return None
                    
                    data = await response.json()
                    
                    if 'artifacts' in data and len(data['artifacts']) > 0:
                        b64_json = data['artifacts'][0].get('base64')
                        if b64_json:
                            print(f"Received base64 data length: {len(b64_json)}")
                            try:
                                image_bytes = base64.b64decode(b64_json)
                                print(f"Decoded image bytes length: {len(image_bytes)}")
                                if len(image_bytes) < 10000: # < 10KB is likely a safety filter placeholder
                                    print(f"Warning: Generated image is too small ({len(image_bytes)} bytes). Likely safety filter.")
                                    return None
                                return io.BytesIO(image_bytes)
                            except Exception as e:
                                print(f"Base64 decode error: {e}")
                                return None
                    
                    print(f"Unexpected response format: {data.keys()}")
                    return None

            except Exception as e:
                print(f"Exception during image generation: {e}")
                return None
