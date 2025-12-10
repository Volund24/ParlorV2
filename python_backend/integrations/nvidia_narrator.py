import aiohttp
from config import settings
import random

STYLES = [
    "a gritty noir detective",
    "a hype-man for a wrestling match",
    "a wise old sage recounting a legend",
    "a fast-talking sports commentator",
    "a dramatic movie trailer voice",
    "a poetic bard",
    "a cyberpunk hacker describing a glitch",
    "a nature documentary narrator"
]

class NvidiaNarrator:
    def __init__(self):
        self.api_key = settings.NVIDIA_API_KEY
        # Using Llama 3.1 405B Instruct via NVIDIA NIM
        self.api_url = "https://integrate.api.nvidia.com/v1/chat/completions"

    async def _generate_text(self, system_prompt, user_prompt):
        if not self.api_key:
            print("Warning: NVIDIA_API_KEY not set.")
            return "Narrator is speechless."

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "model": "meta/llama-3.1-405b-instruct",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.7,
            "top_p": 1,
            "max_tokens": 150
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.api_url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"NVIDIA Text API Error: {response.status} - {error_text}")
                        return "The narrator microphone is broken."
                    
                    data = await response.json()
                    return data['choices'][0]['message']['content']
            except Exception as e:
                print(f"NVIDIA Text Gen Exception: {e}")
                return "The narrator is having technical difficulties."

    async def generate_meeting(self, fighter_a, fighter_b, theme, gender_a=None, gender_b=None, style=None):
        if not style:
            style = random.choice(STYLES)
        g_a = f" ({gender_a})" if gender_a else ""
        g_b = f" ({gender_b})" if gender_b else ""
        system = f"You are {style}. Describe the moment two fighters spot each other in a {theme}. Max 2 sentences. Suspenseful and visual. Note: {fighter_a} is{g_a}, {fighter_b} is{g_b}."
        user = f"{fighter_a} sees their opponent {fighter_b} across the arena."
        return await self._generate_text(system, user)

    async def generate_clash(self, fighter_a, fighter_b, gender_a=None, gender_b=None, style=None):
        if not style:
            style = random.choice(STYLES)
        g_a = f" ({gender_a})" if gender_a else ""
        g_b = f" ({gender_b})" if gender_b else ""
        system = f"You are {style}. Describe the heat of the battle. A story of the clash. Max 2 sentences. High energy. Note: {fighter_a} is{g_a}, {fighter_b} is{g_b}."
        user = f"Describe the intense fight between {fighter_a} and {fighter_b}."
        return await self._generate_text(system, user)

    async def generate_victory(self, winner, loser, gender_winner=None, gender_loser=None, style=None):
        if not style:
            style = random.choice(STYLES)
        g_w = f" ({gender_winner})" if gender_winner else ""
        g_l = f" ({gender_loser})" if gender_loser else ""
        system = f"You are {style}. Declare the winner of the fight. Max 2 sentences. Epic conclusion. Note: {winner} is{g_w}, {loser} is{g_l}."
        user = f"{winner} has defeated {loser}."
        return await self._generate_text(system, user)


