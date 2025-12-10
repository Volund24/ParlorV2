import discord
from discord.ext import commands
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID") # Optional: Sync to specific guild for instant update

if not TOKEN:
    print("❌ Error: DISCORD_TOKEN not found in environment variables.")
    exit(1)

# Initialize Bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user} (ID: {bot.user.id})")
    print("🔄 Starting Command Sync...")

    try:
        # 1. Clear Global Commands (Optional, but good for a full reset)
        # bot.tree.clear_commands(guild=None)
        
        # 2. Sync Global Commands
        # Note: We are syncing an EMPTY tree if we don't load extensions.
        # This effectively wipes the slash commands for this bot, 
        # forcing it to re-register them when the actual bot starts up next time.
        # OR, we can load the extensions here to register the *correct* ones.
        
        # Let's try to load the extensions to register the CURRENT code's commands.
        await load_extensions()
        
        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f"✅ Synced {len(synced)} commands to Guild ID: {GUILD_ID}")
        else:
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} commands GLOBALLY.")
            
        print("🎉 Sync Complete! You can now stop this script and start your main bot.")
        await bot.close()
        
    except Exception as e:
        print(f"❌ Sync Failed: {e}")
        await bot.close()

async def load_extensions():
    # Manually load the cogs we know exist to register their commands
    # Adjust paths if your folder structure on Linode is different
    initial_extensions = [
        'commands.battle',
        'commands.betting',
        'commands.admin',
        'commands.help'
    ]

    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            print(f"  - Loaded extension: {extension}")
        except Exception as e:
            print(f"  - Failed to load extension {extension}: {e}")

if __name__ == "__main__":
    asyncio.run(bot.start(TOKEN))
