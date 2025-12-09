
import asyncio
import os
from config import settings
import google.generativeai as genai

# Force the key from the user's prompt if not in settings
# User provided: sk-9793a1e3-ce7c-47e4-be91-140e0c8f5717 (Wait, that looks like a Supermachine key, not Gemini)
# Gemini keys usually start with AIza...
# The user might have confused the keys.
# Let's check what is in settings.py

async def test_gemini():
    print(f"Checking Gemini API Key...")
    if not settings.GEMINI_API_KEY:
        print("❌ GEMINI_API_KEY is missing in settings.py")
        return

    print(f"Key found: {settings.GEMINI_API_KEY[:5]}...{settings.GEMINI_API_KEY[-5:]}")
    
    genai.configure(api_key=settings.GEMINI_API_KEY)
    
    print("Listing available models...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)
            
    # Try gemini-1.5-flash
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    print("\nTesting Generation (gemini-1.5-flash)...")
    try:
        response = await model.generate_content_async("Say hello in a 90s cartoon style.")
        print(f"✅ Success:\n{response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_gemini())
