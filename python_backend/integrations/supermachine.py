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

        # Pre-process ControlNet image if needed (do this once)
        encoded_control_image = None
        if control_image_url:
            print(f"Downloading control image from: {control_image_url}")
            encoded_control_image = await self._download_and_encode_image(control_image_url)
            if not encoded_control_image:
                print("Skipping ControlNet due to download failure.")

        # Define the race
        RACER_COUNT = 3
        correlation_ids = []

        async def launch_racer(racer_idx):
            correlation_id = str(uuid.uuid4())
            webhook_url = f"{self.webhook_base_url}/webhook/supermachine/{correlation_id}"
            
            payload = {
                "prompt": prompt,
                "modelName": "Supermachine NextGen", 
                "width": 1024,
                "height": 1024,
                "imageNumber": 1,
                "generationMode": "GENERATE",
                "webhookUrl": webhook_url,
            }

            if encoded_control_image:
                payload["refImage"] = encoded_control_image
                payload["controlType"] = "reference_only"
                payload["controlMode"] = "0" # Balance
                payload["controlnetmodule_id"] = "3" # Reference Control

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }

            print(f"🏎️ Racer #{racer_idx} starting... (ID: {correlation_id})")
            
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(self.api_url, json=payload, headers=headers) as response:
                        if response.status != 200:
                            text = await response.text()
                            print(f"Racer #{racer_idx} Crashed: {response.status} - {text}")
                            if response.status == 401:
                                self.access_token = None
                            return None
                        
                        # Register the future
                        loop = asyncio.get_running_loop()
                        future = loop.create_future()
                        self.pending_requests[correlation_id] = future
                        correlation_ids.append(correlation_id)
                        return future
            except Exception as e:
                print(f"Racer #{racer_idx} Exception: {e}")
                return None

        # Launch all racers concurrently
        print(f"🏁 Starting Race with {RACER_COUNT} requests...")
        launch_tasks = [launch_racer(i+1) for i in range(RACER_COUNT)]
        futures = await asyncio.gather(*launch_tasks)
        
        # Filter out any that failed to launch
        valid_futures = [f for f in futures if f is not None]
        
        if not valid_futures:
            print("❌ All racers failed to leave the starting line.")
            return None

        # Wait for the first one to cross the finish line
        try:
            print(f"⏱️ Waiting for the winner...")
            done, pending = await asyncio.wait(valid_futures, return_when=asyncio.FIRST_COMPLETED, timeout=180)
            
            if done:
                winner_future = done.pop()
                image_url = winner_future.result()
                print(f"🏆 We have a winner! URL: {image_url}")
                
                # Cleanup: We don't strictly need to cancel the others, 
                # but we can remove their IDs from pending_requests to keep memory clean
                # (Actually, we can't easily map future -> ID here without extra tracking, 
                # so we'll let handle_webhook clean them up when they eventually arrive or just ignore them)
                
                return await self._download_image(image_url)
            else:
                print("❌ Race timed out. No finishers.")
                # Cleanup pending requests
                for cid in correlation_ids:
                    if cid in self.pending_requests:
                        del self.pending_requests[cid]
                return None

        except Exception as e:
            print(f"Race Critical Error: {e}")
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
