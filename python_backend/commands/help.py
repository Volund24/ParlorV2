import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show available commands")
    async def help_command(self, ctx):
        embed = discord.Embed(title="📜 The Backroom Parlor - Command Guide", color=discord.Color.gold())
        
        embed.add_field(
            name="⚔️ Battle & Tournament",
            value=(
                "`/register` - Join the queue for the next tournament/battle.\n"
                "`/battle` - (Legacy) Start a quick 1v1 or register.\n"
                "`/flex` - Show off your stats or NFT."
            ),
            inline=False
        )
        
        embed.add_field(
            name="💰 Economy & Betting",
            value=(
                "`/bet <amount> <player>` - Place a bet on a match.\n"
                "`/balance` - Check your wallet balance."
            ),
            inline=False
        )
        
        embed.add_field(
            name="ℹ️ Info",
            value=(
                "`/help` - Show this message.\n"
                "`/stats` - View your personal battle record."
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="admin_help", description="Show admin commands")
    @commands.has_permissions(administrator=True)
    async def admin_help(self, ctx):
        embed = discord.Embed(title="🛠️ Admin Command Reference", color=discord.Color.red())
        
        embed.add_field(
            name="🚀 Setup",
            value="`/admin_setup`, `/admin_config`, `/admin_permissions`",
            inline=False
        )
        
        embed.add_field(
            name="💰 Economy",
            value="`/admin_set_token`, `/admin_secondary_token`, `/admin_set_wallet`, `/admin_betting`, `/admin_bet_config`",
            inline=False
        )
        
        embed.add_field(
            name="🎨 Branding",
            value="`/admin_set_theme`, `/admin_set_collection`, `/admin_narrator`",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Tournament",
            value="`/admin_tournament_size`, `/admin_debug_tournament`",
            inline=False
        )
        
        embed.add_field(
            name="📊 Debug",
            value="`/admin_stats`, `/admin_health`, `/admin_kill`",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
