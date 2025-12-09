import discord
from discord.ext import commands
from discord.ui import View, Select, Button
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

# Define our "Collection Style" here
COLLECTION_STYLE = (
    "high quality comic book art, dynamic action shot, vibrant colors, "
    "detailed background, expressive characters, clean lines, cinematic lighting, "
    "graphic novel style, highly detailed"
)

# Random Action Verbs for variety
ACTION_VERBS = ["punching", "kicking", "blasting", "slamming", "dodging", "striking", "grappling"]

class Battle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fairness = FairnessEngine()
        self.narrator = NvidiaNarrator()
        self.nvidia_artist = NvidiaImageGenerator()
        self.vision = NvidiaVision()
        self.supermachine = getattr(bot, 'supermachine', None)
        
        # Tournament Queue
        self.queue = []
        self.tournament_active = False

    def get_config(self):
        # Helper to get admin config
        admin_cog = self.bot.get_cog("Admin")
        if admin_cog:
            return admin_cog.config
        return {"tournament_size": 2, "theme": "Cyberpunk Alleyway"}

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
        img = await self.nvidia_artist.generate_image(prompt) # This method already has Pollinations logic inside
        return img

    @commands.hybrid_command(name='register')
    async def register(self, ctx):
        """Join the queue for the next battle/tournament."""
        if self.tournament_active:
            await ctx.send("⚠️ A tournament is currently in progress. Please wait for the next round.")
            return

        if ctx.author in self.queue:
            await ctx.send("You are already in the queue!")
            return

        self.queue.append(ctx.author)
        
        config = self.get_config()
        required_players = config.get("tournament_size", 2)
        
        # Build the list of registered users
        player_list = "\n".join([f"{i+1}. {p.display_name}" for i, p in enumerate(self.queue)])
        
        embed = discord.Embed(title="📝 Tournament Registration", color=discord.Color.green())
        embed.add_field(name="System Message", value="User has registered for next battle.", inline=False)
        embed.add_field(name=f"Registered Users ({len(self.queue)}/{required_players})", value=player_list if player_list else "None", inline=False)
        embed.set_footer(text=f"Battle will autostart once {required_players} players register.")
        
        await ctx.send(embed=embed)
        
        # Check if we can start
        if len(self.queue) >= required_players:
            await self.start_tournament(ctx)

    @commands.hybrid_command(name='battle')
    async def battle(self, ctx):
        """(Legacy) Register for the battle queue."""
        await self.register(ctx)

    async def start_tournament(self, ctx):
        self.tournament_active = True
        config = self.get_config()
        required_players = config.get("tournament_size", 2)
        
        await ctx.send(f"🚨 **TOURNAMENT STARTING!** 🚨\n{len(self.queue)} fighters have entered the arena!")
        
        # For now, we just take the first 2 players for a 1v1 if size is 2
        # If size > 2, we would need a bracket loop. 
        # Implementing a simple loop for now.
        
        while len(self.queue) >= 2:
            player_a = self.queue.pop(0)
            player_b = self.queue.pop(0)
            
            await ctx.send(f"⚔️ **Match Up:** {player_a.mention} vs {player_b.mention}")
            await self.run_battle(ctx, player_a, player_b)
            
            # Small delay between matches
            await asyncio.sleep(5)
            
        self.tournament_active = False
        if self.queue:
            await ctx.send(f"ℹ️ {len(self.queue)} player(s) remaining in queue waiting for opponents.")

    async def run_battle(self, ctx, player_a, player_b):
        config = self.get_config()
        theme = config.get("theme", "Cyberpunk Alleyway")
        
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
            
            meeting_prompt = (
                f"A comic book panel of ({desc_a}) and ({desc_b}) staring each other down "
                f"in a {theme}, tense atmosphere, split screen composition. {COLLECTION_STYLE}"
            )
            clash_prompt = (
                f"A dynamic comic book panel of ({desc_a}) {action_verb} ({desc_b}) "
                f"in a {theme}, action lines, impact frames, explosion background. {COLLECTION_STYLE}"
            )
            # Explicitly state winner standing over loser
            victory_prompt = (
                f"A comic book panel of ({desc_a if winner == player_a else desc_b}) standing victorious over "
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
            
        except Exception as e:
            print(f"AI Generation Critical Error: {e}")
            import traceback
            traceback.print_exc()
            await update_status(f"❌ **Error:** {str(e)}")
            return

async def setup(bot):
    await bot.add_cog(Battle(bot))
