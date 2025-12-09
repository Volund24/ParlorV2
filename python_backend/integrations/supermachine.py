import aiohttp
import asyncio
import json
import uuid
import base64
import io
from config import settings

class SupermachineImageGenerator:
    def __init__(self):
        self.api_key = settings.SUPERMACHINE_API_KEY
        self.auth_url = "https://api.supermachine.art/v1/auth/token"
        self.api_url = "https://api.supermachine.art/v1/generate"
        self.webhook_base_url = None # Will be set when tunnel starts
        self.pending_requests = {} # correlation_id -> asyncio.Future
        self.access_token = None

    def set_webhook_url(self, url):
        self.webhook_base_url = url
        print(f"Supermachine Webhook URL set to: {url}")

    async def get_access_token(self):
        if self.access_token:
            return self.access_token

        print("Authenticating with Supermachine...")
        try:
            async with aiohttp.ClientSession() as session:
                payload = {"apiKey": self.api_key}
                headers = {"Content-Type": "application/json"}
                
                async with session.post(self.auth_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        text = await response.text()
                        print(f"Supermachine Auth Error: {response.status} - {text}")
                        return None
                    
                    data = await response.json()
                    # The API returns 'authToken'
                    self.access_token = data.get('authToken')
                    if not self.access_token:
                        print(f"Supermachine Auth Failed. Response keys: {data.keys()}")
                        return None
                        
                    print("Supermachine Authentication Successful.")
                    return self.access_token
        except Exception as e:
            print(f"Supermachine Auth Exception: {e}")
            return None

    async def _download_and_encode_image(self, url):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        return base64.b64encode(image_data).decode('utf-8')
                    else:
                        print(f"Failed to download control image: {response.status}")
                        return None
        except Exception as e:
            print(f"Error downloading control image: {e}")
            return None

    async def generate_image(self, prompt, control_image_url=None):
        if not self.webhook_base_url:
            print("Error: Webhook URL not set. Cannot use Supermachine.")
            return None

        token = await self.get_access_token()
        if not token:
            print("Cannot generate image: Authentication failed.")
            return None

        correlation_id = str(uuid.uuid4())
        webhook_url = f"{self.webhook_base_url}/webhook/supermachine/{correlation_id}"
        
        # Base Payload
        payload = {
            "prompt": prompt,
            "modelName": "Supermachine NextGen", 
            "width": 1024,
            "height": 1024,
            "imageNumber": 1,
            "generationMode": "GENERATE",
            "webhookUrl": webhook_url,
        }

        # Add ControlNet if image URL is provided
        if control_image_url:
            print(f"Downloading control image from: {control_image_url}")
            encoded_image = await self._download_and_encode_image(control_image_url)
            if encoded_image:
                payload["refImage"] = encoded_image
                payload["controlType"] = "reference_only"
                payload["controlMode"] = "0" # Balance
                payload["controlnetmodule_id"] = "3" # Reference Control
                print("Added ControlNet parameters to payload.")
            else:
                print("Skipping ControlNet due to download failure.")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }

        print(f"Sending Supermachine request (ID: {correlation_id})...")
        print(f"Webhook URL: {webhook_url}")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, json=payload, headers=headers) as response:
                    if response.status != 200:
                        text = await response.text()
                        print(f"Supermachine API Error: {response.status} - {text}")
                        # If 401, maybe token expired? Reset it.
                        if response.status == 401:
                            self.access_token = None
                        return None
                    
                    data = await response.json()
                    print(f"Supermachine Request Sent. Response: {data}")
                    
                    # Create a future to wait for the webhook
                    loop = asyncio.get_running_loop()
                    future = loop.create_future()
                    self.pending_requests[correlation_id] = future
                    
                    # Wait for the webhook (with timeout)
                    try:
                        print("Waiting for webhook callback...")
                        image_url = await asyncio.wait_for(future, timeout=120) # 2 minute timeout
                        return await self._download_image(image_url)
                    except asyncio.TimeoutError:
                        print(f"Supermachine Timed Out (ID: {correlation_id})")
                        if correlation_id in self.pending_requests:
                            del self.pending_requests[correlation_id]
                        return None

        except Exception as e:
            print(f"Supermachine Exception: {e}")
            return None

    async def handle_webhook(self, correlation_id, data):
        print(f"DEBUG: Webhook Payload Received: {data}") 
        if correlation_id in self.pending_requests:
            print(f"Webhook received for ID: {correlation_id}")
            
            # Inspect data for image URL
            image_url = data.get('url') or data.get('imageUrl') or data.get('output_url')
            
            if not image_url:
                # Check for 'images' array
                if 'images' in data and isinstance(data['images'], list) and len(data['images']) > 0:
                     image_url = data['images'][0].get('url')

            if not image_url:
                print(f"Could not find image URL in webhook data: {data}")
                # Try to find *any* string that looks like a URL
                for key, value in data.items():
                    if isinstance(value, str) and value.startswith("http"):
                        image_url = value
                        break
            
            if image_url:
                self.pending_requests[correlation_id].set_result(image_url)
            else:
                self.pending_requests[correlation_id].set_exception(Exception("No image URL found"))
            
            del self.pending_requests[correlation_id]
        else:
            print(f"Received webhook for unknown ID: {correlation_id}")

    async def _download_image(self, url):
        import io
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return io.BytesIO(await response.read())
        return None
