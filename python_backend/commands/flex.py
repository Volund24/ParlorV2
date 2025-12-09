from discord.ext import commands
import discord

class Flex(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='register')
    async def register(self, ctx):
        """Register your NFT for the next tournament."""
        # Placeholder for actual registration logic
        await ctx.send(f"📝 **{ctx.author.display_name}** has registered for the next tournament!")

    @commands.hybrid_command(name='game_flex')
    async def game_flex(self, ctx):
        """Show off your battle statistics."""
        # Mock data for now - eventually pull from DB
        wins = 5
        losses = 2
        win_rate = (wins / (wins + losses)) * 100
        
        embed = discord.Embed(title=f"💪 Battle Flex: {ctx.author.display_name}", color=discord.Color.gold())
        embed.add_field(name="🏆 Wins", value=str(wins), inline=True)
        embed.add_field(name="💀 Losses", value=str(losses), inline=True)
        embed.add_field(name="📈 Win Rate", value=f"{win_rate:.1f}%", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name='bet_flex')
    async def bet_flex(self, ctx):
        """Show off your betting history."""
        # Mock data for now
        total_wagered = 1500
        net_profit = 450
        
        embed = discord.Embed(title=f"💸 Betting Flex: {ctx.author.display_name}", color=discord.Color.green())
        embed.add_field(name="💰 Total Wagered", value=f"{total_wagered} SOL", inline=True)
        embed.add_field(name="🤑 Net Profit", value=f"+{net_profit} SOL", inline=True)
        embed.add_field(name="🎲 Biggest Win", value="200 SOL", inline=True)
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Flex(bot))
