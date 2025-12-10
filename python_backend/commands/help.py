import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Show available commands")
    async def help_command(self, ctx):
        embed = discord.Embed(title="📜 The Backroom Parlor - Command Guide", color=discord.Color.gold())
        
        embed.add_field(
            name="⚔️ Battle Arena",
            value=(
                "`/battle [opponent]` - Challenge a user to a 1v1 deathmatch. (1 per day)\n"
                "`/register` - Host or join a Tournament (Royale or Gang War).\n"
                "`/how_to_play` - Learn the rules of the Parlor."
            ),
            inline=False
        )
        
        embed.add_field(
            name="💰 Betting & Economy",
            value=(
                "`/bet <amount> <player>` - Wager tokens on active matches.\n"
                "`/balance` - Check your token stash.\n"
                "`/stats` - View your win/loss record."
            ),
            inline=False
        )
        
        embed.set_footer(text="Use /admin_help for staff commands.")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="how_to_play", description="Learn the rules of Battle Royale and Gang Wars")
    async def how_to_play(self, ctx):
        embed = discord.Embed(title="📖 How to Play", color=discord.Color.blurple())
        
        embed.add_field(
            name="🥊 1v1 Duels",
            value=(
                "Use `/battle` to fight an instant duel.\n"
                "• You can challenge a specific user or let the bot pick a random opponent.\n"
                "• **Limit:** You can only fight **once every 24 hours** (unless you are an Admin)."
            ),
            inline=False
        )
        
        embed.add_field(
            name="🏆 Battle Royale",
            value=(
                "Use `/register` to start a tournament.\n"
                "• **8 Players** enter a bracket.\n"
                "• Winners advance, losers are eliminated.\n"
                "• The last fighter standing wins the pot!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="⚔️ Gang Wars",
            value=(
                "Use `/register` and select **Gang Battle**.\n"
                "• Pick a side (Team A vs Team B).\n"
                "• Teams fight in a series of 1v1s.\n"
                "• The team with the most wins takes the glory!"
            ),
            inline=False
        )
        
        embed.add_field(
            name="💸 Betting",
            value=(
                "Spectators can bet on matches using `/bet`.\n"
                "• Odds are calculated based on fighter stats.\n"
                "• Winners get paid from the loser's pool!"
            ),
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="admin_help", description="Show admin commands")
    @commands.has_permissions(administrator=True)
    async def admin_help(self, ctx):
        embed = discord.Embed(title="🛠️ Admin Command Reference", color=discord.Color.red())
        
        embed.add_field(
            name="🚀 Setup & Reset",
            value=(
                "`/admin_setup` - Initialize server config.\n"
                "`/admin_reset` - **Soft Reset:** Clears queue AND resets everyone's daily 1v1 limit.\n"
                "`/admin_restart` - **Hard Restart:** Reboots the bot."
            ),
            inline=False
        )
        
        embed.add_field(
            name="💰 Economy",
            value="`/admin_set_token`, `/admin_give_token`, `/admin_betting`",
            inline=False
        )
        
        embed.add_field(
            name="🎨 Customization",
            value="`/admin_set_theme`, `/admin_narrator`",
            inline=False
        )
        
        embed.add_field(
            name="🏆 Tournament Debug",
            value="`/admin_debug_tournament` - Simulates a full tournament with bots.",
            inline=False
        )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
