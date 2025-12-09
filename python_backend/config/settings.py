import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
SUPERMACHINE_API_KEY = os.getenv("SUPERMACHINE_API_KEY", "sk-9793a1e3-ce7c-47e4-be91-140e0c8f5717")
SOLANA_RPC_URL = os.getenv("SOLANA_RPC_URL")
ADMIN_ID = os.getenv("ADMIN_ID")
DISCORD_GUILD_ID = os.getenv("DISCORD_GUILD_ID")
