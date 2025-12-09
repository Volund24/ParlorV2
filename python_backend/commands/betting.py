from discord.ext import commands

class Betting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name='bet')
    async def bet(self, ctx, amount: float, player_name: str):
        await ctx.send(f"Betting {amount} on {player_name} not implemented yet.")

async def setup(bot):
    await bot.add_cog(Betting(bot))
