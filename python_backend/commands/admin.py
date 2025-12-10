import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from engine.fighter import Fighter
from database.db_manager import get_db
from database.models import Player

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

    @commands.command(name="admin_sync", description="Sync slash commands with Discord")
    @commands.has_permissions(administrator=True)
    async def admin_sync(self, ctx):
        """Force sync slash commands."""
        await ctx.send("🔄 Syncing commands...")
        try:
            synced = await self.bot.tree.sync()
            await ctx.send(f"✅ Synced {len(synced)} commands globally.")
        except Exception as e:
            await ctx.send(f"❌ Sync failed: {e}")

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

    @commands.hybrid_command(name="admin_give_token", description="Give tokens to a user (Faucet)")
    @commands.has_permissions(administrator=True)
    async def admin_give_token(self, ctx, member: discord.Member, amount: float):
        if not self.config.get("payout_token"):
            await ctx.send("❌ No payout token set! Use `/admin_set_token` first.")
            return
            
        betting_cog = self.bot.get_cog("Betting")
        if not betting_cog:
            await ctx.send("❌ Betting module not loaded.")
            return
            
        betting_cog.add_balance(member.id, amount)
        await ctx.send(f"💸 Sent **{amount} {self.config['payout_token']}** to {member.mention}")

    @commands.hybrid_command(name="admin_debug_tournament", description="Test tournament flow")
    @commands.has_permissions(administrator=True)
    async def admin_debug_tournament(self, ctx):
        await ctx.send("🧪 **Debug Tournament**\nSimulating registration of 8 Pepe fighters...")
        
        battle_cog = self.bot.get_cog("Battle")
        if not battle_cog:
            await ctx.send("❌ Battle module not loaded.")
            return

        # Reset Queue
        battle_cog.queue = []
        battle_cog.tournament_mode = 'ROYALE'
        battle_cog.debug_mode = True
        
        # Mock Member Class
        class MockMember:
            def __init__(self, name, user_id):
                self.display_name = name
                self.name = name
                self.id = user_id
                self.display_avatar = type('obj', (object,), {'url': "https://i.imgur.com/8nLFCVP.png"}) # Pepe Image
                self.mention = f"**{name}**"
                self.status = discord.Status.online
                self.bot = False

        # Create 8 Pepe Fighters
        pepes = [
            Fighter(MockMember("Pepe A", 1001)),
            Fighter(MockMember("Pepe B", 1002)),
            Fighter(MockMember("Pepe C", 1003)),
            Fighter(MockMember("Pepe D", 1004)),
            Fighter(MockMember("Pepe E", 1005)),
            Fighter(MockMember("Pepe F", 1006)),
            Fighter(MockMember("Pepe G", 1007)),
            Fighter(MockMember("Pepe H", 1008))
        ]
        
        battle_cog.queue.extend(pepes)
        
        await ctx.send(f"✅ Registered {len(pepes)} fighters. Starting bracket...")
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

    @commands.hybrid_command(name="admin_reset", description="Soft Reset: Clears tournament state and 1v1 timers")
    @commands.has_permissions(administrator=True)
    async def admin_reset(self, ctx):
        """Resets the Battle Cog state and clears daily 1v1 limits for all players."""
        battle_cog = self.bot.get_cog("Battle")
        if not battle_cog:
            return await ctx.send("❌ Battle module not loaded.")
        
        # Reset Tournament State
        battle_cog.queue = []
        battle_cog.tournament_active = False
        battle_cog.current_match_id = None
        battle_cog.tournament_mode = None
        battle_cog.team_rosters = {'A': [], 'B': []}
        battle_cog.team_names = {'A': 'Team A', 'B': 'Team B'}
        
        # Reset 1v1 Timers in DB
        db_gen = get_db()
        db = next(db_gen)
        try:
            # Set last_1v1_battle_at to NULL for all players
            db.query(Player).update({Player.last_1v1_battle_at: None})
            db.commit()
            db_msg = "✅ Daily 1v1 limits reset for all players."
        except Exception as e:
            db_msg = f"⚠️ Failed to reset DB timers: {e}"
        finally:
            try:
                next(db_gen)
            except StopIteration:
                pass

        await ctx.send(f"🔄 **System Reset Complete!**\n✅ Tournament Queue cleared.\n{db_msg}")

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
