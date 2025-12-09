import random

class LocalNarrator:
    def __init__(self):
        self.meeting_templates = [
            "{a} ({species_a}) locks eyes with {b} ({species_b})! The air crackles with tension!",
            "It's {a} vs {b}! A {species_a} against a {species_b} in the {theme}!",
            "{a} steps into the {theme}, ready to crush {b}!",
            "The crowd goes silent as {a} and {b} face off!",
            "A {species_a} and a {species_b} walk into a {theme}... only one walks out!",
            "{a} sneers at {b}. This is going to be ugly!",
            "Sparks fly as {a} and {b} prepare for battle!",
            "In the red corner: {a}! In the blue corner: {b}!",
            "{a} flexes. {b} laughs. It's go time!",
            "The {theme} isn't big enough for both {a} and {b}!"
        ]
        
        self.clash_templates = [
            "BAM! {a} lands a massive hit on {b}!",
            "KA-POW! {b} gets sent flying by {a}!",
            "It's total chaos! Explosions everywhere!",
            "{a} and {b} are tearing the {theme} apart!",
            "CRUNCH! That looked painful for {b}!",
            "ZAP! {a} unleashes a secret move!",
            "SMASH! {b} is on the ropes!",
            "Blood, sweat, and pixels! What a fight!",
            "{a} is relentless! {b} is struggling to keep up!",
            "BOOM! A massive explosion rocks the arena!"
        ]
        
        self.victory_templates = [
            "{winner} stands triumphant! What a victory!",
            "{winner} is the champion of the {theme}!",
            "Flawless victory for {winner}!",
            "{loser} is down for the count! {winner} wins!",
            "Hail to the king, baby! {winner} takes the crown!",
            "{winner} poses on the defeated body of {loser}!",
            "Game Over for {loser}! {winner} reigns supreme!",
            "{winner} proves that {winner_species}s are superior!",
            "Total domination by {winner}!",
            "And the winner is... {winner}!"
        ]

    async def generate_meeting(self, fighter_a, fighter_b, theme, species_a, species_b):
        template = random.choice(self.meeting_templates)
        return template.format(a=fighter_a, b=fighter_b, theme=theme, species_a=species_a, species_b=species_b)

    async def generate_clash(self, fighter_a, fighter_b, species_a, species_b):
        template = random.choice(self.clash_templates)
        return template.format(a=fighter_a, b=fighter_b)

    async def generate_victory(self, winner, loser, winner_species, loser_species):
        template = random.choice(self.victory_templates)
        return template.format(winner=winner, loser=loser, winner_species=winner_species)
