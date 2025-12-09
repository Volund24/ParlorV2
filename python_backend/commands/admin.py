import discord
from discord.ext import commands
from discord import app_commands
import json
import os

# Default Configuration
DEFAULT_CONFIG = {
    "tournament_size": 8, # Default to smallest tournament size
    "payout_token": "SOL",
    "secondary_token": None,
    "treasury_wallet": None,
    "betting_enabled": False,
    "betting_min": 0.1,
    "betting_max": 10.0,
    "house_edge": 0.05,
    "theme": "cyberpunk",
    "nft_collection": "None",
    "narrator_style": "Dynamic"
}

CONFIG_FILE = "server_config.json"

class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return DEFAULT_CONFIG.copy()

    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=4)

    def is_admin(self, interaction: discord.Interaction):
        return interaction.user.guild_permissions.administrator

    # --- Setup & Config ---

    @commands.hybrid_command(name="admin_setup", description="First-time server configuration")
    @commands.has_permissions(administrator=True)
    async def admin_setup(self, ctx):
        """Interactive setup for the server."""
        await ctx.send("🛠️ **Admin Setup**\nInitializing default configuration...")
        self.config = DEFAULT_CONFIG.copy()
        self.save_config()
        await ctx.send("✅ Configuration reset to defaults.\nUse `/admin_config` to view settings.")

    @commands.hybrid_command(name="admin_config", description="View current server settings")
    @commands.has_permissions(administrator=True)
    async def admin_config(self, ctx):
        """View the current configuration."""
        embed = discord.Embed(title="⚙️ Server Configuration", color=discord.Color.greyple())
        for key, value in self.config.items():
            embed.add_field(name=key.replace("_", " ").title(), value=str(value), inline=True)
        await ctx.send(embed=embed)

    # --- Token & Economy ---

    @commands.hybrid_command(name="admin_set_token", description="Configure primary payout token")
    @commands.has_permissions(administrator=True)
    async def admin_set_token(self, ctx, symbol: str):
        self.config["payout_token"] = symbol.upper()
        self.save_config()
        await ctx.send(f"✅ Primary token set to **{symbol.upper()}**")

    @commands.hybrid_command(name="admin_secondary_token", description="Enable dual-token payouts")
    @commands.has_permissions(administrator=True)
    async def admin_secondary_token(self, ctx, symbol: str = None):
        if symbol:
            self.config["secondary_token"] = symbol.upper()
            await ctx.send(f"✅ Secondary token set to **{symbol.upper()}**")
        else:
            self.config["secondary_token"] = None
            await ctx.send("✅ Secondary token disabled.")
        self.save_config()

    @commands.hybrid_command(name="admin_set_wallet", description="Set server treasury wallet")
    @commands.has_permissions(administrator=True)
    async def admin_set_wallet(self, ctx, address: str):
        self.config["treasury_wallet"] = address
        self.save_config()
        await ctx.send(f"✅ Treasury wallet set to `{address}`")

    @commands.hybrid_command(name="admin_betting", description="Enable/disable betting")
    @commands.has_permissions(administrator=True)
    async def admin_betting(self, ctx, enabled: bool):
        self.config["betting_enabled"] = enabled
        self.save_config()
        status = "Enabled" if enabled else "Disabled"
        await ctx.send(f"✅ Betting is now **{status}**")

    @commands.hybrid_command(name="admin_bet_config", description="Configure betting limits")
    @commands.has_permissions(administrator=True)
    async def admin_bet_config(self, ctx, min_bet: float, max_bet: float, house_edge: float):
        self.config["betting_min"] = min_bet
        self.config["betting_max"] = max_bet
        self.config["house_edge"] = house_edge
        self.save_config()
        await ctx.send(f"✅ Betting configured: Min {min_bet}, Max {max_bet}, Edge {house_edge*100}%")

    # --- Branding & NFTs ---

    @commands.hybrid_command(name="admin_set_theme", description="Choose visual theme")
    @commands.has_permissions(administrator=True)
    async def admin_set_theme(self, ctx, theme: str):
        self.config["theme"] = theme
        self.save_config()
        await ctx.send(f"✅ Theme set to **{theme}**")

    @commands.hybrid_command(name="admin_set_collection", description="Set NFT collection for battles")
    @commands.has_permissions(administrator=True)
    async def admin_set_collection(self, ctx, collection_name: str):
        self.config["nft_collection"] = collection_name
        self.save_config()
        await ctx.send(f"✅ NFT Collection set to **{collection_name}**")

    @commands.hybrid_command(name="admin_narrator", description="Configure match commentary style")
    @commands.has_permissions(administrator=True)
    async def admin_narrator(self, ctx, style: str):
        self.config["narrator_style"] = style
        self.save_config()
        await ctx.send(f"✅ Narrator style set to **{style}**")

    # --- Tournament Management ---

    @commands.hybrid_command(name="admin_tournament_size", description="Set bracket size")
    @commands.has_permissions(administrator=True)
    async def admin_tournament_size(self, ctx, size: int):
        if size not in [2, 4, 8, 16, 32]:
            await ctx.send("❌ Invalid size. Please choose 2, 4, 8, 16, or 32.")
            return
        self.config["tournament_size"] = size
        self.save_config()
        await ctx.send(f"✅ Tournament size set to **{size}** players.")

    @commands.hybrid_command(name="admin_debug_tournament", description="Test tournament flow")
    @commands.has_permissions(administrator=True)
    async def admin_debug_tournament(self, ctx):
        await ctx.send("🧪 **Debug Tournament**\nSimulating registration of dummy players...")
        # Logic to inject dummy players into the battle cog would go here
        # For now, just a message
        await ctx.send("⚠️ Feature not fully implemented yet.")

    # --- Monitoring & Debug ---

    @commands.hybrid_command(name="admin_stats", description="View server statistics")
    @commands.has_permissions(administrator=True)
    async def admin_stats(self, ctx):
        await ctx.send("📊 **Server Stats**\nBattles Run: 0\nTotal Volume: 0 SOL")

    @commands.hybrid_command(name="admin_health", description="Check bot status")
    @commands.has_permissions(administrator=True)
    async def admin_health(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.send(f"💚 **System Healthy**\nLatency: {latency}ms\nDatabase: Connected")

    @commands.hybrid_command(name="admin_kill", description="Emergency shutdown")
    @commands.has_permissions(administrator=True)
    async def admin_kill(self, ctx):
        await ctx.send("🛑 **Emergency Shutdown Initiated...**")
        await self.bot.close()

async def setup(bot):
    await bot.add_cog(Admin(bot))
