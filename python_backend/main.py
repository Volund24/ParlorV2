import discord
from discord.ext import commands
from config import settings
import asyncio
import os
from aiohttp import web
from integrations.supermachine import SupermachineImageGenerator

# Initialize Supermachine Generator (Global)
supermachine_gen = SupermachineImageGenerator()
# Set the Webhook URL from environment variable or default to localtunnel
webhook_url = os.getenv("WEBHOOK_URL", "https://rare-pots-leave.loca.lt")
supermachine_gen.set_webhook_url(webhook_url)

# Intent setup
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix='/', intents=intents, help_command=None)

# --- Webhook Server ---
async def handle_webhook(request):
    print(f"🔔 WEBHOOK HIT: {request.path}")
    correlation_id = request.match_info.get('id')
    try:
        data = await request.json()
        print(f"📦 WEBHOOK DATA ({correlation_id}): {data}")
        await supermachine_gen.handle_webhook(correlation_id, data)
        return web.Response(text="OK")
    except Exception as e:
        print(f"❌ Webhook Error: {e}")
        return web.Response(status=500)

async def handle_ping(request):
    return web.Response(text="Pong! Tunnel is active.")

async def start_web_server():
    app = web.Application()
    app.router.add_post('/webhook/supermachine/{id}', handle_webhook)
    app.router.add_get('/ping', handle_ping)
    app.router.add_get('/', handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 3000)
    await site.start()
    print("Webhook Server started on port 3000")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    
    # Inject the supermachine generator into the bot so cogs can access it
    bot.supermachine = supermachine_gen
    
    try:
        if settings.DISCORD_GUILD_ID:
            guild = discord.Object(id=settings.DISCORD_GUILD_ID)
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f'Synced {len(synced)} commands to guild {settings.DISCORD_GUILD_ID}')
        else:
            synced = await bot.tree.sync()
            print(f'Synced {len(synced)} commands globally')
    except Exception as e:
        print(f'Failed to sync commands: {e}')
    print('------')

async def load_extensions():
    # Load extensions/cogs here
    await bot.load_extension('commands.battle')
    await bot.load_extension('commands.flex')
    await bot.load_extension('commands.betting')
    await bot.load_extension('commands.admin')
    await bot.load_extension('commands.help')


async def main():
    # Start Web Server
    await start_web_server()
    
    # Inject Supermachine BEFORE loading extensions so Cogs can access it
    bot.supermachine = supermachine_gen
    
    async with bot:
        await load_extensions()
        if settings.DISCORD_TOKEN:
            await bot.start(settings.DISCORD_TOKEN)
        else:
            print("Error: DISCORD_TOKEN not found in environment variables.")

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        pass
