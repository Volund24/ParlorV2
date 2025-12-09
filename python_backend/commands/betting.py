import discord
from discord.ext import commands
import asyncio
import time

class BettingEngine:
    def __init__(self):
        self.active_bets = {} # match_id -> {user_id: {amount, player}}
        self.pools = {} # match_id -> {player_a: total, player_b: total}
        self.is_open = {} # match_id -> bool
        self.odds = {} # match_id -> {player_a: multiplier, player_b: multiplier}

    def open_market(self, match_id):
        self.active_bets[match_id] = {}
        self.pools[match_id] = {'A': 0.0, 'B': 0.0}
        self.is_open[match_id] = True
        self.odds[match_id] = {'A': 1.0, 'B': 1.0}

    def close_market(self, match_id):
        self.is_open[match_id] = False
        # Calculate final odds
        pool_a = self.pools[match_id]['A']
        pool_b = self.pools[match_id]['B']
        total_pool = pool_a + pool_b
        
        if pool_a > 0:
            self.odds[match_id]['A'] = total_pool / pool_a
        if pool_b > 0:
            self.odds[match_id]['B'] = total_pool / pool_b

    def place_bet(self, match_id, user, amount, team):
        if not self.is_open.get(match_id):
            return False, "Betting is closed for this match."
        
        # In a real app, check user balance here
        
        if match_id not in self.active_bets:
            self.active_bets[match_id] = {}
            
        self.active_bets[match_id][user.id] = {'amount': amount, 'team': team, 'user_name': user.display_name}
        self.pools[match_id][team] += amount
        return True, f"Bet placed: {amount} on {team}"

    def resolve(self, match_id, winning_team):
        winners = []
        if match_id not in self.active_bets:
            return []

        odds = self.odds[match_id].get(winning_team, 1.0)
        
        for user_id, bet in self.active_bets[match_id].items():
            if bet['team'] == winning_team:
                winnings = bet['amount'] * odds
                winners.append({
                    'user_name': bet['user_name'],
                    'winnings': winnings,
                    'profit': winnings - bet['amount']
                })
                # In a real app, credit user balance here
        
        # Cleanup
        del self.active_bets[match_id]
        del self.pools[match_id]
        del self.is_open[match_id]
        del self.odds[match_id]
        
        return winners

class Betting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.engine = BettingEngine()
        self.user_balances = {} # Mock DB for now: user_id -> float

    def get_balance(self, user_id):
        return self.user_balances.get(user_id, 100.0) # Default 100 tokens

    def add_balance(self, user_id, amount):
        self.user_balances[user_id] = self.get_balance(user_id) + amount

    @commands.hybrid_command(name='balance')
    async def balance(self, ctx):
        """Check your token balance."""
        bal = self.get_balance(ctx.author.id)
        await ctx.send(f"💰 **Wallet:** {bal:.2f} Tokens")

    @commands.hybrid_command(name='bet')
    async def bet(self, ctx, amount: float, team: str):
        """Place a bet on the current match. Usage: /bet 10 A (or B)"""
        # Find active match (simplified: assuming 1 active match per server for now)
        # In reality, we'd need to know which match context we are in.
        # For now, we'll let the Battle Cog manage the "Current Match ID"
        
        battle_cog = self.bot.get_cog("Battle")
        if not battle_cog or not battle_cog.current_match_id:
            await ctx.send("⚠️ No active match to bet on.")
            return

        match_id = battle_cog.current_match_id
        
        # Validate Team
        team = team.upper()
        if team not in ['A', 'B']:
             await ctx.send("⚠️ Invalid selection. Bet on 'A' or 'B'.")
             return

        # Validate Balance
        bal = self.get_balance(ctx.author.id)
        if amount > bal:
            await ctx.send(f"❌ Insufficient funds. Balance: {bal}")
            return

        success, msg = self.engine.place_bet(match_id, ctx.author, amount, team)
        if success:
            self.add_balance(ctx.author.id, -amount)
            await ctx.send(f"✅ {msg}")
        else:
            await ctx.send(f"❌ {msg}")

    # Admin Commands for Testing
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def admin_give_tokens(self, ctx, member: discord.Member, amount: float):
        self.add_balance(member.id, amount)
        await ctx.send(f"💸 Added {amount} tokens to {member.display_name}.")

async def setup(bot):
    await bot.add_cog(Betting(bot))
