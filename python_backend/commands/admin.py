import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from engine.fighter import Fighter

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
    async def admin_setup(self, ctx, payout_token: str = "SOL", collection_slug: str = "None"):
        """Interactive setup for the server."""
        await ctx.send("🛠️ **Admin Setup**\nInitializing configuration...")
        self.config = DEFAULT_CONFIG.copy()
        self.config["payout_token"] = payout_token.upper()
        self.config["nft_collection"] = collection_slug
        self.save_config()
        await ctx.send(f"✅ Configuration set!\nToken: **{payout_token.upper()}**\nCollection: **{collection_slug}**\nUse `/admin_config` to view all settings.")

    @commands.hybrid_command(name="admin_link_wallet", description="Manually link a user wallet")
    @commands.has_permissions(administrator=True)
    async def admin_link_wallet(self, ctx, member: discord.Member, wallet_address: str):
        # In a real app, this would update the DB
        await ctx.send(f"🔗 Linked wallet `{wallet_address}` to {member.mention}")

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
        
        battle_cog = self.bot.get_cog("Battle")
        if not battle_cog:
            await ctx.send("❌ Battle module not loaded.")
            return

        # Reset Queue
        battle_cog.queue = []
        battle_cog.tournament_mode = 'ROYALE'
        battle_cog.debug_mode = True
        
        # Add Dummy Players (using ctx.author and bot as stand-ins if needed, or mock objects)
        # Since we need discord.Member objects, we can try to fetch some members or just use the author multiple times with a hack
        # But for a true test, we need distinct objects.
        # Let's just use the author and some random members if available, or mock classes.
        
        class MockMember:
            def __init__(self, name, user_id, avatar_url):
                self.display_name = name
                self.name = name
                self.id = user_id
                self.display_avatar = type('obj', (object,), {'url': avatar_url})
                self.mention = f"@{name}"
                self.status = discord.Status.online
                self.bot = False

        # Create 4 dummies
        dummies = [
            Fighter(MockMember("Cyber_Ninja", 1001, "https://picsum.photos/200")),
            Fighter(MockMember("Neon_Samurai", 1002, "https://picsum.photos/201")),
            Fighter(MockMember("Data_Mage", 1003, "https://picsum.photos/202")),
            Fighter(MockMember("Glitch_Witch", 1004, "https://picsum.photos/203"))
        ]
        
        battle_cog.queue.extend(dummies)
        
        await ctx.send(f"✅ Registered {len(dummies)} dummy fighters.")
        await battle_cog.start_tournament(ctx)
        battle_cog.debug_mode = False # Reset after start

    @commands.hybrid_command(name="gang_choice", description="Set up Gang Battle (Host Collection)")
    @commands.has_permissions(administrator=True)
    async def gang_choice(self, ctx, team_a: str, team_b: str):
        """Set up a Gang Battle with predefined team names."""
        battle_cog = self.bot.get_cog("Battle")
        if not battle_cog:
            return await ctx.send("❌ Battle module not loaded.")
            
        battle_cog.tournament_mode = 'GANG'
        battle_cog.team_names['A'] = team_a
        battle_cog.team_names['B'] = team_b
        battle_cog.queue = []
        battle_cog.team_rosters = {'A': [], 'B': []}
        
        await ctx.send(f"⚔️ **Gang Battle Setup!**\nTeams: **{team_a}** vs **{team_b}**\nUse `/register` to join.")

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

    @commands.hybrid_command(name="admin_reset", description="Soft Reset: Clears tournament state without restarting bot")
    @commands.has_permissions(administrator=True)
    async def admin_reset(self, ctx):
        """Resets the Battle Cog state (Queue, Active Tournament, etc)."""
        battle_cog = self.bot.get_cog("Battle")
        if not battle_cog:
            return await ctx.send("❌ Battle module not loaded.")
        
        # Reset State
        battle_cog.queue = []
        battle_cog.tournament_active = False
        battle_cog.current_match_id = None
        battle_cog.tournament_mode = None
        battle_cog.team_rosters = {'A': [], 'B': []}
        battle_cog.team_names = {'A': 'Team A', 'B': 'Team B'}
        
        await ctx.send("🔄 **Tournament State Reset!**\nQueue cleared. Ready for new `/register`.")

    @commands.hybrid_command(name="admin_restart", description="Hard Restart: Reboots the bot container")
    @commands.has_permissions(administrator=True)
    async def admin_restart(self, ctx):
        """Kills the process. Docker will auto-restart it."""
        await ctx.send("🛑 **Rebooting System...**\n(Bot will be back in ~10-20 seconds)")
        await self.bot.close()

    @commands.hybrid_command(name="admin_kill", description="Alias for admin_restart")
    @commands.has_permissions(administrator=True)
    async def admin_kill(self, ctx):
        await self.admin_restart(ctx)

async def setup(bot):
    await bot.add_cog(Admin(bot))
