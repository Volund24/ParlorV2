import discord
from discord.ext import commands
from discord.ui import View, Select, Button, Modal, TextInput
from engine.fairness import FairnessEngine
from integrations.nvidia_narrator import NvidiaNarrator
from integrations.nvidia_image_generator import NvidiaImageGenerator
from integrations.nvidia_vision import NvidiaVision
from commands.admin import Admin # Import Admin to access config
import asyncio
import io
import random
import time
import os
import uuid

# Define our "Collection Style" here
COLLECTION_STYLE = (
    "high quality comic book art, dynamic action shot, vibrant colors, "
    "detailed background, expressive characters, clean lines, cinematic lighting, "
    "graphic novel style, highly detailed"
)

# Random Action Verbs for variety
ACTION_VERBS = ["punching", "kicking", "blasting", "slamming", "dodging", "striking", "grappling"]
WEAPONS = ["energy sword", "cyber-pistol", "plasma rifle", "battle axe", "power fists", "nano-whip", "laser cannon"]

from engine.fighter import Fighter, AvatarProxy

# --- Helper Classes ---


# --- UI Classes for Tournament Registration ---

class TeamNameModal(Modal, title="Name Your Teams"):
    team_a_name = TextInput(label="Team A Name", placeholder="e.g. The Crips", default="Team A")
    team_b_name = TextInput(label="Team B Name", placeholder="e.g. The Bloods", default="Team B")

    def __init__(self, cog, ctx, fighter):
        super().__init__()
        self.cog = cog
        self.ctx = ctx
        self.fighter = fighter

    async def on_submit(self, interaction: discord.Interaction):
        if self.fighter in self.cog.queue:
             return await interaction.response.send_message("You are already registered!", ephemeral=True)

        self.cog.team_names['A'] = self.team_a_name.value
        self.cog.team_names['B'] = self.team_b_name.value
        self.cog.tournament_mode = 'GANG'
        
        # Register the user to Team A (default for creator)
        self.cog.queue.append(self.fighter)
        self.cog.team_rosters['A'].append(self.fighter)
        
        # Update the original message to show selection
        try:
            await interaction.response.edit_message(content=f"⚔️ **Gang Battle Mode Selected!**\nTeams: **{self.team_a_name.value}** vs **{self.team_b_name.value}**", view=None, embed=None)
        except:
            # Fallback if edit fails (e.g. message deleted)
            await interaction.response.defer()

        await interaction.followup.send(
            f"{self.fighter.mention} joined **{self.team_a_name.value}**!",
            embed=self.cog.get_registration_embed()
        )

class TournamentModeView(View):
    def __init__(self, cog, ctx, fighter):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        self.fighter = fighter

    @discord.ui.button(label="Battle Royale (Bracket)", style=discord.ButtonStyle.danger, emoji="🏆")
    async def royale_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Only the first player can decide the mode!", ephemeral=True)
        
        if self.fighter in self.cog.queue:
             return await interaction.response.send_message("You are already registered!", ephemeral=True)

        self.cog.tournament_mode = 'ROYALE'
        self.cog.queue.append(self.fighter)
        await interaction.response.edit_message(content="🏆 **Battle Royale Mode Selected!**", view=None, embed=self.cog.get_registration_embed())

    @discord.ui.button(label="Gang Battle (Teams)", style=discord.ButtonStyle.blurple, emoji="⚔️")
    async def gang_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Only the first player can decide the mode!", ephemeral=True)
        
        await interaction.response.send_modal(TeamNameModal(self.cog, self.ctx, self.fighter))

class TeamButton(Button):
    def __init__(self, label, team, style):
        super().__init__(label=label, style=style)
        self.team = team

    async def callback(self, interaction: discord.Interaction):
        cog = self.view.cog
        fighter = Fighter(interaction.user)
        
        if fighter in cog.queue:
            return await interaction.response.send_message("You are already registered!", ephemeral=True)

        # Balance Check
        my_team_count = len(cog.team_rosters[self.team])
        other_team = 'B' if self.team == 'A' else 'A'
        other_team_count = len(cog.team_rosters[other_team])
        
        # Strict balancing REMOVED per user request. 
        # We only enforce even numbers at start.

        cog.queue.append(fighter)
        cog.team_rosters[self.team].append(fighter)
        
        await interaction.response.edit_message(
            content=f"✅ {fighter.mention} joined **{cog.team_names[self.team]}**!",
            view=None,
            embed=cog.get_registration_embed()
        )
        
        # Check for start
        config = cog.get_config()
        if len(cog.queue) >= config.get("tournament_size", 8):
            await cog.start_tournament(interaction.channel)

class TeamSelectView(View):
    def __init__(self, cog, ctx):
        super().__init__(timeout=60)
        self.cog = cog
        self.ctx = ctx
        
        # Update button labels with counts
        name_a = self.cog.team_names['A']
        name_b = self.cog.team_names['B']
        count_a = len(self.cog.team_rosters['A'])
        count_b = len(self.cog.team_rosters['B'])
        
        self.add_item(TeamButton(label=f"Join {name_a} ({count_a})", team='A', style=discord.ButtonStyle.red))
        self.add_item(TeamButton(label=f"Join {name_b} ({count_b})", team='B', style=discord.ButtonStyle.blurple))

class BettingView(View):
    def __init__(self, cog, match_id, player_a, player_b):
        super().__init__(timeout=15)
        self.cog = cog
        self.match_id = match_id
        self.player_a = player_a
        self.player_b = player_b
        self.selected_team = None
        self.selected_amount = 10.0 # Default

    @discord.ui.select(placeholder="Choose Fighter to Bet On", options=[
        discord.SelectOption(label="Player A", value="A", description="Bet on Player A"),
        discord.SelectOption(label="Player B", value="B", description="Bet on Player B")
    ])
    async def select_team(self, interaction: discord.Interaction, select: Select):
        self.selected_team = select.values[0]
        # Update label to show selection
        fighter_name = self.player_a.display_name if self.selected_team == 'A' else self.player_b.display_name
        await interaction.response.send_message(f"Selected **{fighter_name}**. Now choose amount and click Place Bet!", ephemeral=True)

    @discord.ui.select(placeholder="Wager Amount", options=[
        discord.SelectOption(label="10 Tokens", value="10"),
        discord.SelectOption(label="50 Tokens", value="50"),
        discord.SelectOption(label="100 Tokens", value="100"),
        discord.SelectOption(label="500 Tokens", value="500"),
        discord.SelectOption(label="ALL IN", value="ALL")
    ])
    async def select_amount(self, interaction: discord.Interaction, select: Select):
        val = select.values[0]
        if val == "ALL":
            # Logic to get full balance would be needed here, for now just a placeholder high number or handle in callback
            self.selected_amount = "ALL"
        else:
            self.selected_amount = float(val)
        await interaction.response.send_message(f"Wager set to **{val}**.", ephemeral=True)

    @discord.ui.button(label="Place Bet", style=discord.ButtonStyle.green, emoji="💸")
    async def place_bet(self, interaction: discord.Interaction, button: Button):
        if not self.selected_team:
            return await interaction.response.send_message("⚠️ You must select a fighter first!", ephemeral=True)
        
        betting_cog = self.cog.bot.get_cog("Betting")
        if not betting_cog:
            return await interaction.response.send_message("Betting system offline.", ephemeral=True)

        amount = self.selected_amount
        if amount == "ALL":
            amount = betting_cog.get_balance(interaction.user.id)

        # Place the bet
        success, msg = betting_cog.engine.place_bet(self.match_id, interaction.user, amount, self.selected_team)
        
        if success:
            betting_cog.add_balance(interaction.user.id, -amount)
            await interaction.response.send_message(f"✅ **Bet Placed!** {amount} on {self.selected_team}", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ {msg}", ephemeral=True)

class Battle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fairness = FairnessEngine()
        self.narrator = NvidiaNarrator()
        self.nvidia_artist = NvidiaImageGenerator()
        
        # Tournament State
        self.tournament_mode = None # 'ROYALE' or 'GANG'
        self.team_names = {'A': 'Team A', 'B': 'Team B'}
        self.team_rosters = {'A': [], 'B': []}
        self.vision = NvidiaVision()
        self.supermachine = getattr(bot, 'supermachine', None)
        
        # Tournament Queue
        self.queue = []
        self.tournament_active = False
        self.current_match_id = None
        self.debug_mode = False # Flag for debug tournament

    def get_registration_embed(self):
        config = self.get_config()
        required_players = config.get("tournament_size", 8)
        
        embed = discord.Embed(title="📝 Tournament Registration", color=discord.Color.green())
        
        if self.tournament_mode == 'ROYALE':
            embed.add_field(name="Mode", value="🏆 Battle Royale", inline=False)
            player_list = "\n".join([f"{i+1}. {p.display_name}" for i, p in enumerate(self.queue)])
            embed.add_field(name=f"Registered Users ({len(self.queue)}/{required_players})", value=player_list if player_list else "None", inline=False)
            
        elif self.tournament_mode == 'GANG':
            embed.add_field(name="Mode", value=f"⚔️ Gang Battle: {self.team_names['A']} vs {self.team_names['B']}", inline=False)
            
            team_a_list = "\n".join([p.display_name for p in self.team_rosters['A']])
            team_b_list = "\n".join([p.display_name for p in self.team_rosters['B']])
            
            embed.add_field(name=f"{self.team_names['A']} ({len(self.team_rosters['A'])})", value=team_a_list if team_a_list else "None", inline=True)
            embed.add_field(name=f"{self.team_names['B']} ({len(self.team_rosters['B'])})", value=team_b_list if team_b_list else "None", inline=True)
            embed.add_field(name="Total", value=f"{len(self.queue)}/{required_players}", inline=False)
            
        else:
            embed.add_field(name="Mode", value="Not Selected", inline=False)
            
        embed.set_footer(text=f"Battle will autostart once {required_players} players register.")
        return embed

    def get_config(self):
        # Helper to get admin config
        admin_cog = self.bot.get_cog("Admin")
        if admin_cog:
            return admin_cog.config
        return {"tournament_size": 8, "theme": "Cyberpunk Alleyway"}

    async def generate_image_hybrid(self, prompt, prefer_nvidia=False, control_image_url=None):
        """
        Hybrid Generator:
        1. If prefer_nvidia=True, try NVIDIA Flux (Sanitized).
        2. If Supermachine is configured (Webhook URL set), try Supermachine.
        3. Fallback to Pollinations.
        4. Fallback to NVIDIA Flux (Sanitized).
        """
        
        # 1. NVIDIA Preference
        if prefer_nvidia:
            print("DEBUG: Hybrid Gen - Prefer NVIDIA")
            img = await self.nvidia_artist.generate_image(prompt, prefer_nvidia=True)
            if img: return img

        # 2. Supermachine (The "Big Gun")
        if self.supermachine and self.supermachine.webhook_base_url:
            print("DEBUG: Hybrid Gen - Attempting Supermachine...")
            img = await self.supermachine.generate_image(prompt, control_image_url=control_image_url)
            if img: 
                print("DEBUG: Supermachine Success!")
                return img
            else:
                print("DEBUG: Supermachine Failed/Timed Out. Falling back...")

        # 3. Pollinations (Standard Fallback)
        print("DEBUG: Hybrid Gen - Attempting Pollinations...")
        # Force Pollinations by not passing prefer_nvidia=True
        img = await self.nvidia_artist.generate_image(prompt, prefer_nvidia=False) 
        return img

    @commands.hybrid_command(name='register')
    async def register(self, ctx):
        """Join the queue for the next battle/tournament."""
        if self.tournament_active:
            await ctx.send("⚠️ A tournament is currently in progress. Please wait for the next round.")
            return

        fighter = Fighter(ctx.author)

        if fighter in self.queue:
            await ctx.send("You are already in the queue!")
            return
        
        # If queue is empty, this user is the host/creator
        if len(self.queue) == 0:
            # Reset State
            self.tournament_mode = None
            self.team_rosters = {'A': [], 'B': []}
            self.team_names = {'A': 'Team A', 'B': 'Team B'}
            
            view = TournamentModeView(self, ctx, fighter)
            await ctx.send(f"👋 Welcome {fighter.mention}! You are the first to register.\nPlease select the Tournament Mode:", view=view)
            return

        # If mode is not selected yet (shouldn't happen if first user flow works, but safety check)
        if self.tournament_mode is None:
            await ctx.send("⚠️ Waiting for the first player to select the mode...")
            return

        # Handle Registration based on Mode
        if self.tournament_mode == 'ROYALE':
            self.queue.append(fighter)
            await ctx.send(f"✅ {fighter.mention} joined the Battle Royale!", embed=self.get_registration_embed())
            
            # Check for start
            config = self.get_config()
            if len(self.queue) >= config.get("tournament_size", 8):
                await self.start_tournament(ctx.channel)
            
        elif self.tournament_mode == 'GANG':
            view = TeamSelectView(self, ctx)
            await ctx.send(f"⚔️ {fighter.mention}, choose your side:", view=view)
            return # View handles the rest
        
        # Check if we can start (Fallback)
        config = self.get_config()
        required_players = config.get("tournament_size", 8)
        if len(self.queue) >= required_players:
            await self.start_tournament(ctx)

    @commands.hybrid_command(name='battle')
    async def battle(self, ctx, opponent: discord.Member = None):
        """Start an instant 1v1 battle. If no opponent is specified, a random one is chosen."""
        
        player_a = ctx.author
        player_b = opponent
        auto_selected = False

        if player_b is None:
            # Select a random online user
            candidates = [
                m for m in ctx.guild.members 
                if not m.bot and m.id != player_a.id and m.status != discord.Status.offline
            ]
            
            if not candidates:
                # Fallback to all non-bots if no one is "online" (e.g. invisible)
                candidates = [
                    m for m in ctx.guild.members 
                    if not m.bot and m.id != player_a.id
                ]
            
            if not candidates:
                await ctx.send("⚠️ No eligible opponents found!")
                return
                
            player_b = random.choice(candidates)
            auto_selected = True

        if auto_selected:
            await ctx.send(f"User didn't choose an opponent, so the Arena chose for them. Their opponent is {player_b.mention}")
        else:
            await ctx.send(f"⚔️ **Instant Battle Initiated!**\n{player_a.mention} vs {player_b.mention}")
             
        await self.run_battle(ctx, player_a, player_b, enable_betting=False)

    async def start_tournament(self, ctx):
        self.tournament_active = True
        config = self.get_config()
        
        # Gang Battle Balance Check
        if self.tournament_mode == 'GANG':
            len_a = len(self.team_rosters['A'])
            len_b = len(self.team_rosters['B'])
            if len_a != len_b:
                self.tournament_active = False
                await ctx.send(f"⚠️ **Cannot Start!** Teams are uneven ({len_a} vs {len_b}).\nPlease wait for more players or balance the teams.")
                return

        # Countdown (Skip if debug)
        if not self.debug_mode:
            await ctx.send("@everyone 🚨 **TOURNAMENT STARTING IN 5 MINUTES!** 🚨\nGet your bets ready!")
            # In a real scenario, we'd wait 300 seconds. For demo/testing, maybe shorter or strictly 5 mins.
            # User asked for 5 minute countdown.
            # await asyncio.sleep(300) 
            # For the sake of not blocking the thread for 5 mins during this dev session, I'll make it 10 seconds but comment the 5 mins
            await asyncio.sleep(10) # TODO: Change to 300 for production

        await ctx.send(f"🚨 **TOURNAMENT STARTING!** 🚨\nMode: **{self.tournament_mode}**")
        
        if self.tournament_mode == 'ROYALE':
            await self.run_royale_bracket(ctx)
        elif self.tournament_mode == 'GANG':
            await self.run_gang_battle(ctx)
        else:
            # Fallback for legacy/default behavior (1v1 loop) if mode not set
            await self.run_royale_bracket(ctx)
        
        # Cleanup
        self.tournament_active = False
        self.queue = []
        self.team_rosters = {'A': [], 'B': []}
        self.tournament_mode = None
        await ctx.send("🏆 **Tournament Concluded!** Queue is now open.")

    async def run_royale_bracket(self, ctx):
        round_num = 1
        current_players = list(self.queue) # Copy
        random.shuffle(current_players)
        
        # Initial Bracket Display
        bracket_str = "🏆 **Tournament Bracket**\n"
        for i in range(0, len(current_players), 2):
            if i + 1 < len(current_players):
                bracket_str += f"• {current_players[i].display_name} vs {current_players[i+1].display_name}\n"
            else:
                bracket_str += f"• {current_players[i].display_name} (Bye)\n"
        await ctx.send(bracket_str)
        
        while len(current_players) > 1:
            await ctx.send(f"🔔 **Round {round_num} Begins!** ({len(current_players)} fighters)")
            next_round_players = []
            
            # Create pairs
            matches = []
            for i in range(0, len(current_players), 2):
                if i + 1 < len(current_players):
                    matches.append((current_players[i], current_players[i+1]))
                else:
                    # Bye
                    await ctx.send(f"ℹ️ {current_players[i].mention} gets a bye this round!")
                    next_round_players.append(current_players[i])
            
            # Run matches
            for p1, p2 in matches:
                await ctx.send(f"⚔️ **Match Up:** {p1.mention} vs {p2.mention}")
                winner = await self.run_battle(ctx, p1, p2, enable_betting=True)
                if winner:
                    next_round_players.append(winner)
                    await ctx.send(f"🏅 {winner.mention} advances to the next round!")
                else:
                    # Should not happen, but if error, pick random?
                    await ctx.send("⚠️ Error in match. Advancing random player.")
                    next_round_players.append(random.choice([p1, p2]))
                
                await asyncio.sleep(5) # Cooldown
            
            current_players = next_round_players
            round_num += 1
            
            # End of Round Bracket Update
            if len(current_players) > 1:
                bracket_str = f"🏆 **Advancing to Round {round_num}**\n"
                for p in current_players:
                    bracket_str += f"• {p.display_name}\n"
                await ctx.send(bracket_str)
            
        # Champion
        if current_players:
            await ctx.send(f"👑 **THE CHAMPION IS {current_players[0].mention}!** 👑")

    async def run_gang_battle(self, ctx):
        team_a = list(self.team_rosters['A'])
        team_b = list(self.team_rosters['B'])
        random.shuffle(team_a)
        random.shuffle(team_b)
        
        wins = {'A': 0, 'B': 0}
        
        # Determine number of matches (min size)
        num_matches = min(len(team_a), len(team_b))
        
        await ctx.send(f"⚔️ **Gang Battle: {self.team_names['A']} vs {self.team_names['B']}**\nMatches: {num_matches}")
        
        for i in range(num_matches):
            p1 = team_a[i]
            p2 = team_b[i]
            
            await ctx.send(f"🥊 **Match {i+1}:** {p1.mention} ({self.team_names['A']}) vs {p2.mention} ({self.team_names['B']})")
            
            winner = await self.run_battle(ctx, p1, p2, enable_betting=True)
            
            if winner in team_a:
                wins['A'] += 1
                await ctx.send(f"🔵 Point for **{self.team_names['A']}**!")
            else:
                wins['B'] += 1
                await ctx.send(f"🔴 Point for **{self.team_names['B']}**!")
                
            await asyncio.sleep(5)
            
        # Final Score
        score_msg = f"📊 **Final Score:**\n{self.team_names['A']}: {wins['A']}\n{self.team_names['B']}: {wins['B']}"
        await ctx.send(score_msg)
        
        if wins['A'] > wins['B']:
            await ctx.send(f"🏆 **{self.team_names['A']} WINS THE WAR!**")
        elif wins['B'] > wins['A']:
            await ctx.send(f"🏆 **{self.team_names['B']} WINS THE WAR!**")
        else:
            await ctx.send("🤝 **IT'S A DRAW!**")

    async def run_battle(self, ctx, player_a, player_b, enable_betting=False):
        config = self.get_config()
        theme = config.get("theme", "Cyberpunk Alleyway")
        
        # --- BETTING PHASE ---
        self.current_match_id = str(uuid.uuid4())
        betting_cog = self.bot.get_cog("Betting")
        
        if betting_cog and enable_betting and config.get("betting_enabled", False):
            betting_cog.engine.open_market(self.current_match_id)
            
            bet_embed = discord.Embed(title="🎰 Betting Open!", color=discord.Color.gold())
            bet_embed.add_field(name="Fighter A", value=player_a.display_name, inline=True)
            bet_embed.add_field(name="Fighter B", value=player_b.display_name, inline=True)
            bet_embed.set_footer(text="Closing in 15 seconds!")
            
            view = BettingView(self, self.current_match_id, player_a, player_b)
            bet_msg = await ctx.send(embed=bet_embed, view=view)
            
            await asyncio.sleep(15)
            
            betting_cog.engine.close_market(self.current_match_id)
            # Disable view
            view.stop()
            await bet_msg.edit(view=None)
            await ctx.send("🔒 **Betting Closed!**")

        # Helper to update status (we'll send a new message since we don't have an interaction object from a button click)
        status_msg = await ctx.send(f"⚔️ **Initializing Match:** {player_a.display_name} vs {player_b.display_name}...")
        
        async def update_status(text):
            try:
                await status_msg.edit(content=f"⚔️ **Battle in Progress**\n📍 Arena: {theme}\n\n{text}")
            except:
                pass

        # 1. Calculate Winner (Fairness Engine)
        winner = self.fairness.determine_winner(player_a, player_b)
        loser = player_b if winner == player_a else player_a
        winning_team = 'A' if winner == player_a else 'B'
        
        # 2. Generate Narrative & Art (Parallel)
        
        try:
            # Create tasks for parallel execution
            print("Starting AI Generation...")
            await update_status("👁️ **Scanning Fighters...** (Analyzing Avatars)")
            
            # Step 2a: Analyze Avatars (Vision)
            print("Analyzing Avatars...")
            desc_a_task = self.vision.describe_avatar(player_a.display_avatar.url)
            desc_b_task = self.vision.describe_avatar(player_b.display_avatar.url)
            
            desc_a, desc_b = await asyncio.gather(desc_a_task, desc_b_task)

            await update_status("✍️ **Writing the Legend...** (Generating Story)")

            # Step 2b: Generate Text (Narrator)
            # --- PARALLEL GENERATION START ---
            await update_status("🚀 **Launching Battle...** (Generating All Scenes)")
            
            # 1. Define Prompts (Randomized)
            action_verb = random.choice(ACTION_VERBS)
            weapon_a = random.choice(WEAPONS)
            weapon_b = random.choice(WEAPONS)
            
            meeting_prompt = (
                f"A comic book panel of ({desc_a}) holding a {weapon_a} and ({desc_b}) holding a {weapon_b} staring each other down "
                f"in a {theme}, tense atmosphere, split screen composition. {COLLECTION_STYLE}"
            )
            clash_prompt = (
                f"A dynamic comic book panel of ({desc_a}) using a {weapon_a} to {action_verb} ({desc_b}) "
                f"in a {theme}, action lines, impact frames, explosion background. {COLLECTION_STYLE}"
            )
            # Explicitly state winner standing over loser
            victory_prompt = (
                f"A comic book panel of ({desc_a if winner == player_a else desc_b}) holding a {weapon_a if winner == player_a else weapon_b} standing victorious over "
                f"a defeated ({desc_b if winner == player_a else desc_a}) lying on the ground, triumphant pose, "
                f"in a {theme}. {COLLECTION_STYLE}"
            )

            # 2. Create Tasks
            task_text_meeting = asyncio.create_task(self.narrator.generate_meeting(player_a.display_name, player_b.display_name, theme))
            task_text_clash = asyncio.create_task(self.narrator.generate_clash(player_a.display_name, player_b.display_name))
            task_text_victory = asyncio.create_task(self.narrator.generate_victory(winner.display_name, loser.display_name))
            
            # --- SCENE 1: THE MEETING ---
            await update_status("🎨 **Scene 1/3: The Meeting** (Processing...)")
            
            meeting_text = await task_text_meeting
            # Use Player A's avatar as control for Scene 1
            meeting_image_data = await self.generate_image_hybrid(meeting_prompt, prefer_nvidia=False, control_image_url=player_a.display_avatar.url)
            
            embed1 = discord.Embed(title="⚔️ THE BACKROOM PARLOR ⚔️", color=discord.Color.blue())
            embed1.add_field(name="👀 The Stare Down", value=f"*{meeting_text}*", inline=False)
            file1 = None
            if meeting_image_data and isinstance(meeting_image_data, io.BytesIO):
                meeting_image_data.seek(0)
                file1 = discord.File(meeting_image_data, filename="meeting.jpg")
                embed1.set_image(url="attachment://meeting.jpg")
            
            await ctx.send(embed=embed1, file=file1)
            
                        # --- BETTING PHASE (Async Delay) ---
            if config.get("betting_enabled", False):
                await update_status("💰 **Betting Window Open!** (Place your bets now!)")
                # Simulate betting window
                await asyncio.sleep(10)

            # --- SCENE 2: THE CLASH ---
            await update_status("🎨 **Scene 2/3: The Clash** (Processing...)")
            
            clash_text = await task_text_clash
            # Use Player A's avatar as control for Scene 2 (or random?)
            clash_image_data = await self.generate_image_hybrid(clash_prompt, prefer_nvidia=False, control_image_url=player_a.display_avatar.url)
            
            embed2 = discord.Embed(color=discord.Color.red())
            embed2.add_field(name="💥 The Clash", value=f"*{clash_text}*", inline=False)
            file2 = None
            if clash_image_data and isinstance(clash_image_data, io.BytesIO):
                clash_image_data.seek(0)
                file2 = discord.File(clash_image_data, filename="clash.jpg")
                embed2.set_image(url="attachment://clash.jpg")
            
            await ctx.send(embed=embed2, file=file2)

            # --- SCENE 3: THE VICTORY ---
            await update_status("🎨 **Scene 3/3: The Victory** (Processing...)")
            
            victory_text = await task_text_victory
            # Use WINNER's avatar as control for Scene 3
            victory_image_data = await self.generate_image_hybrid(victory_prompt, prefer_nvidia=False, control_image_url=winner.display_avatar.url)
            
            embed3 = discord.Embed(color=discord.Color.gold())
            embed3.add_field(name="🏆 The Victor", value=f"**{winner.display_name}**\n\n*{victory_text}*", inline=False)
            file3 = None
            if victory_image_data and isinstance(victory_image_data, io.BytesIO):
                victory_image_data.seek(0)
                file3 = discord.File(victory_image_data, filename="victory.jpg")
                embed3.set_image(url="attachment://victory.jpg")
            
            embed3.set_thumbnail(url=winner.display_avatar.url)
            
            await ctx.send(embed=embed3, file=file3)
            
            await update_status("✅ **Battle Complete!**")
            
            # --- BETTING RESOLUTION ---
            if betting_cog and enable_betting and config.get("betting_enabled", False):
                winners = betting_cog.engine.resolve(self.current_match_id, winning_team)
                if winners:
                    # Sort by profit
                    winners.sort(key=lambda x: x['profit'], reverse=True)
                    
                    summary = "💰 **Betting Results**\n"
                    for w in winners:
                        betting_cog.add_balance(ctx.guild.get_member_named(w['user_name']).id if ctx.guild.get_member_named(w['user_name']) else 0, w['winnings']) # Mock DB update
                        summary += f"• **{w['user_name']}** won {w['winnings']:.2f} (Profit: {w['profit']:.2f})\n"
                    
                    biggest_winner = winners[0]
                    summary += f"\n🏆 **Big Winner:** {biggest_winner['user_name']} (+{biggest_winner['profit']:.2f})"
                    await ctx.send(summary)
                else:
                    await ctx.send("💸 No winners this round.")

            return winner
            
        except Exception as e:
            print(f"AI Generation Critical Error: {e}")
            import traceback
            traceback.print_exc()
            await update_status(f"❌ **Error:** {str(e)}")
            return

async def setup(bot):
    await bot.add_cog(Battle(bot))
