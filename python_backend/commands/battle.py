import discord
from discord.ext import commands
from discord.ui import View, Select, Button
from engine.fairness import FairnessEngine
from integrations.nvidia_narrator import NvidiaNarrator # Switched to NvidiaNarrator
from integrations.nvidia_image_generator import NvidiaImageGenerator
from integrations.nvidia_vision import NvidiaVision
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

class BattleSetupView(View):
    def __init__(self, ctx, opponent, battle_cog):
        super().__init__(timeout=60)
        self.ctx = ctx
        self.opponent = opponent
        self.battle_cog = battle_cog
        self.selected_arena = "Cyberpunk Alleyway"
        self.selected_gender = "They/Them"
        
        # Arena Select
        self.arena_select = Select(
            placeholder="Choose an Arena...",
            options=[
                discord.SelectOption(label="Cyberpunk Alleyway", description="Neon lights and rain"),
                discord.SelectOption(label="Medieval Colosseum", description="Sand and stone"),
                discord.SelectOption(label="Space Station", description="Zero gravity and stars"),
                discord.SelectOption(label="Haunted Forest", description="Mist and shadows"),
                discord.SelectOption(label="Volcanic Crater", description="Lava and ash"),
            ]
        )
        self.arena_select.callback = self.arena_callback
        self.add_item(self.arena_select)

        
        # Creature Select (Replaced with NFT/PFP Select)
        self.creature_select = Select(
            placeholder="Select Your Fighter's Avatar...",
            options=[
                discord.SelectOption(label="The Growerz", description="Cannabis culture avatar"),
                discord.SelectOption(label="Gainz", description="Fitness & muscle avatar"),
                discord.SelectOption(label="MNK3YS", description="Pixelated monkey avatar"),
                discord.SelectOption(label="Stoned Ape Crew", description="Chilled out ape"),
                discord.SelectOption(label="Bored Ape", description="Classic BAYC style"),
                discord.SelectOption(label="CryptoPunk", description="OG Pixel art"),
                discord.SelectOption(label="Custom PFP", description="Use your current profile picture"),
            ]
        )
        self.creature_select.callback = self.creature_callback
        self.add_item(self.creature_select)

        # Start Button
        self.start_button = Button(label="⚔️ Start Battle", style=discord.ButtonStyle.danger)
        self.start_button.callback = self.start_callback
        self.add_item(self.start_button)

    async def arena_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)
        self.selected_arena = self.arena_select.values[0]
        await interaction.response.defer()

    async def creature_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)
        self.selected_gender = self.creature_select.values[0] # Reusing variable name for minimal refactor
        await interaction.response.defer()

    async def start_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)
        
        try:
            # Determine Avatar URL
            avatar_url = None
            if self.selected_gender == "Custom PFP":
                avatar_url = self.ctx.author.display_avatar.url

            # Update message to show loading state
            await interaction.response.edit_message(content=f"⚔️ **Battle Starting!**\n📍 Arena: {self.selected_arena}\n🧬 Avatar: {self.selected_gender}\n\n🔄 **Initializing Battle Engine...**", view=None)
            
            # Trigger the actual battle logic, passing the interaction for updates
            await self.battle_cog.run_battle(self.ctx, self.opponent, self.selected_arena, self.selected_gender, interaction, avatar_url=avatar_url)
        except Exception as e:
            print(f"Start Battle Error: {e}")
            import traceback
            traceback.print_exc()
            # Try to send a message if interaction is still valid
            try:
                await interaction.followup.send(f"❌ Failed to start battle: {e}", ephemeral=True)
            except:
                pass


        # Start Button
        self.start_button = Button(label="⚔️ Start Battle", style=discord.ButtonStyle.danger)
        self.start_button.callback = self.start_callback
        self.add_item(self.start_button)

    async def arena_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)
        self.selected_arena = self.arena_select.values[0]
        await interaction.response.defer()

    async def creature_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)
        self.selected_gender = self.creature_select.values[0] # Reusing variable name for minimal refactor
        await interaction.response.defer()

    async def start_callback(self, interaction: discord.Interaction):
        if interaction.user != self.ctx.author:
            return await interaction.response.send_message("Not your battle!", ephemeral=True)
        
        # Update message to show loading state
        await interaction.response.edit_message(content=f"⚔️ **Battle Starting!**\n📍 Arena: {self.selected_arena}\n🧬 Species: {self.selected_gender}\n\n🔄 **Initializing Battle Engine...**", view=None)
        
        # Trigger the actual battle logic, passing the interaction for updates
        await self.battle_cog.run_battle(self.ctx, self.opponent, self.selected_arena, self.selected_gender, interaction)

class Battle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.fairness = FairnessEngine()
        self.narrator = NvidiaNarrator() # Switched to Nvidia
        self.nvidia_artist = NvidiaImageGenerator()
        self.vision = NvidiaVision()
        # Supermachine is injected into bot in main.py
        self.supermachine = getattr(bot, 'supermachine', None)

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

    @commands.hybrid_command(name='battle')
    async def battle(self, ctx, opponent: discord.Member = None):
        """Start a battle against another user. If no opponent is specified, one will be chosen at random."""
        
        if not opponent:
            potential_opponents = [m for m in ctx.guild.members if not m.bot and m.id != ctx.author.id]
            if not potential_opponents:
                await ctx.send("There's no one else here to fight! Invite some friends.")
                return
            opponent = random.choice(potential_opponents)
            await ctx.send(f"🎲 **{ctx.author.display_name}** didn't pick a fight, so the arena chose **{opponent.display_name}**!")

        if opponent.id == ctx.author.id:
            await ctx.send("You can't fight yourself!")
            return

        # Send the Setup View
        view = BattleSetupView(ctx, opponent, self)
        await ctx.send(f"⚔️ **{ctx.author.display_name}** vs **{opponent.display_name}**\nConfigure your battle:", view=view)

    async def run_battle(self, ctx, opponent, theme, player_gender, interaction=None, avatar_url=None):
        player_a = ctx.author
        player_b = opponent
        
        # Helper to update status
        async def update_status(text):
            if interaction:
                try:
                    await interaction.edit_original_response(content=f"⚔️ **Battle in Progress**\n📍 Arena: {theme}\n\n{text}")
                except:
                    pass # Ignore if message deleted or too old

        # Default opponent gender to unknown/they
        opponent_gender = "They/Them" 

        # 1. Calculate Winner (Fairness Engine)
        winner = self.fairness.determine_winner(player_a, player_b)
        
        # 2. Generate Narrative & Art (Parallel)
        # theme is passed from view
        
        intro_text = f"**{player_a.display_name}** vs **{player_b.display_name}**!"
        action_text = "BAM! POW!"
        victory_text = f"**{winner.display_name}** wins!"
        
        meeting_image_data = None
        clash_image_data = None
        victory_image_data = None

        try:
            # Create tasks for parallel execution
            print("Starting AI Generation...")
            await update_status("👁️ **Scanning Fighters...** (Analyzing Avatars)")
            
            # Step 2a: Analyze Avatars (Vision)
            print("Analyzing Avatars...")
            desc_a_task = self.vision.describe_avatar(player_a.display_avatar.url)
            desc_b_task = self.vision.describe_avatar(opponent.display_avatar.url)
            
            desc_a, desc_b = await asyncio.gather(desc_a_task, desc_b_task)
            print(f"Avatar A: {desc_a}")
            print(f"Avatar B: {desc_b}")

            await update_status("✍️ **Writing the Legend...** (Generating Story)")

            # Step 2b: Generate Text (Narrator)
            # Using Gemini Narrator for more variety
            loser = player_b if winner == player_a else player_a
            winner_species = player_gender if winner == player_a else opponent_gender
            loser_species = opponent_gender if winner == player_a else player_gender
            
            # --- PARALLEL GENERATION START ---
            await update_status("🚀 **Launching Battle...** (Generating All Scenes)")
            
            # 1. Define Prompts
            meeting_prompt = (
                f"A comic book panel of ({desc_a}, {player_gender}) and ({desc_b}) staring each other down "
                f"in a {theme}, tense atmosphere, split screen composition. {COLLECTION_STYLE}"
            )
            clash_prompt = (
                f"A dynamic comic book panel of ({desc_a}, {player_gender}) fighting ({desc_b}) "
                f"in a {theme}, action lines, impact frames, explosion background. {COLLECTION_STYLE}"
            )
            victory_prompt = (
                f"A comic book panel of ({desc_a if winner == player_a else desc_b}, {winner_species}) standing victorious over "
                f"({desc_b if winner == player_a else desc_a}), triumphant pose, "
                f"in a {theme}. {COLLECTION_STYLE}"
            )

            # 2. Create Tasks
            # Text Tasks (Keep these parallel as they are fast)
            task_text_meeting = asyncio.create_task(self.narrator.generate_meeting(player_a.display_name, player_b.display_name, theme, player_gender, opponent_gender))
            task_text_clash = asyncio.create_task(self.narrator.generate_clash(player_a.display_name, player_b.display_name, player_gender, opponent_gender))
            task_text_victory = asyncio.create_task(self.narrator.generate_victory(winner.display_name, loser.display_name, winner_species, loser_species))
            
            # Image Tasks - SEQUENTIAL to avoid timeouts/rate limits
            # Scene 1: Supermachine (First priority)
            # task_img_meeting = asyncio.create_task(self.generate_image_hybrid(meeting_prompt, prefer_nvidia=False))
            
            # --- SCENE 1: THE MEETING ---
            await update_status("🎨 **Scene 1/3: The Meeting** (Processing...)")
            
            meeting_text = await task_text_meeting
            # Generate Image 1 (Use Supermachine/Pollinations for consistency/uncensored)
            # Use avatar_url if available (Player A is in the scene)
            meeting_image_data = await self.generate_image_hybrid(meeting_prompt, prefer_nvidia=False, control_image_url=avatar_url)
            
            embed1 = discord.Embed(title="⚔️ THE BACKROOM PARLOR ⚔️", color=discord.Color.blue())
            embed1.add_field(name="👀 The Stare Down", value=f"*{meeting_text}*", inline=False)
            file1 = None
            if meeting_image_data and isinstance(meeting_image_data, io.BytesIO):
                meeting_image_data.seek(0)
                file1 = discord.File(meeting_image_data, filename="meeting.jpg")
                embed1.set_image(url="attachment://meeting.jpg")
            
            await ctx.send(embed=embed1, file=file1)
            
            # --- SCENE 2: THE CLASH ---
            await update_status("🎨 **Scene 2/3: The Clash** (Processing...)")
            
            clash_text = await task_text_clash
            # Generate Image 2
            # Use avatar_url if available
            clash_image_data = await self.generate_image_hybrid(clash_prompt, prefer_nvidia=False, control_image_url=avatar_url)
            
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
            # Generate Image 3
            # Only use avatar_url if Player A is the winner to avoid confusion
            victory_control_url = avatar_url if (winner == player_a) else None
            victory_image_data = await self.generate_image_hybrid(victory_prompt, prefer_nvidia=False, control_image_url=victory_control_url)
            
            embed3 = discord.Embed(color=discord.Color.gold())
            embed3.add_field(name="🏆 The Victor", value=f"**{winner.display_name}**\n\n*{victory_text}*", inline=False)
            file3 = None
            if victory_image_data and isinstance(victory_image_data, io.BytesIO):
                victory_image_data.seek(0)
                file3 = discord.File(victory_image_data, filename="victory.jpg")
                embed3.set_image(url="attachment://victory.jpg")
            
            if winner == ctx.author:
                embed3.set_thumbnail(url=ctx.author.display_avatar.url)
            else:
                embed3.set_thumbnail(url=opponent.display_avatar.url)
            
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
