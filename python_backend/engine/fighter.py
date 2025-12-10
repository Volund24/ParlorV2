import discord
import random

class AvatarProxy:
    def __init__(self, url):
        self.url = url

class Fighter:
    def __init__(self, member, custom_url=None):
        self.member = member
        self.custom_url = custom_url
        
        # NFT / Deck Management
        self.nfts = [] # List of {name, image_url, rarity_rank, mint}
        self.spent_nfts = set() # Set of mint addresses used in this tournament
        self.is_pepe = False
        self.current_nft = None # The active NFT for the current round
        
        # Loot (Reset every round)
        self.current_loot = None # {name, bonus_points, rarity}

    def prepare_for_round(self):
        """
        Selects the next available NFT or falls back to Pepe.
        Generates random loot for the round.
        """
        # 1. Select NFT
        available_nfts = [n for n in self.nfts if n['mint'] not in self.spent_nfts]
        
        if available_nfts:
            # Auto-select best rank? Or random? User said "User can only choose PFP in 1v1... ALL BATTLE ROYALES MUST USE NFT"
            # Assuming auto-select best for now to give advantage, or just first available.
            # Let's sort by rarity (lower rank is better usually, but depends on data. Assuming 1 is best)
            # If no rarity data, just pick first.
            available_nfts.sort(key=lambda x: x.get('rarity_rank', 999999))
            self.current_nft = available_nfts[0]
            self.spent_nfts.add(self.current_nft['mint'])
            self.is_pepe = False
        else:
            # Fallback to Pepe
            self.is_pepe = True
            self.current_nft = {
                'name': "Pepe the Frog",
                'image_url': "https://i.imgur.com/8nLFCVP.png", # Default Pepe
                'rarity_rank': 999999,
                'mint': 'pepe_fallback'
            }
            
            # 50/50 Chance for Pepe Bro vs Pepe Jeet
            if random.random() > 0.5:
                self.current_nft['name'] = "Pepe Bro"
                self.current_nft['pepe_type'] = "BRO"
            else:
                self.current_nft['name'] = "Pepe Jeet"
                self.current_nft['pepe_type'] = "JEET"

        # 2. Generate Loot (20% Chance)
        self.current_loot = None
        if random.random() < 0.20:
            self.current_loot = self._generate_loot()

    def _generate_loot(self):
        """Generates a random loot item."""
        loot_table = [
            {'name': "Rusty Shiv", 'bonus': 50, 'rarity': 'Common'},
            {'name': "Energy Drink", 'bonus': 100, 'rarity': 'Uncommon'},
            {'name': "Laser Sight", 'bonus': 200, 'rarity': 'Rare'},
            {'name': "Cybernetic Eye", 'bonus': 350, 'rarity': 'Epic'},
            {'name': "Never-Ending Lighter", 'bonus': 450, 'rarity': 'Mythic'}
        ]
        # Weighted random could be better, but simple choice for now
        return random.choice(loot_table)

    @property
    def display_name(self):
        if self.current_nft:
            name = self.current_nft['name']
            if self.current_loot:
                # Don't show loot in name to keep it secret? User said "Loot stats... hidden until AFTER tournament"
                # But maybe a visual cue? "Pepe Bro (Equipped)"?
                # For now, keep it secret.
                pass
            return f"{self.member.display_name} ({name})"
        return self.member.display_name
        
    @property
    def mention(self):
        return self.member.mention
        
    @property
    def id(self):
        return self.member.id
        
    @property
    def name(self):
        return self.member.name

    @property
    def display_avatar(self):
        if self.current_nft and self.current_nft.get('image_url'):
            return AvatarProxy(self.current_nft['image_url'])
        if self.custom_url:
            return AvatarProxy(self.custom_url)
        return self.member.display_avatar
        
    def __eq__(self, other):
        if isinstance(other, Fighter):
            return self.member.id == other.member.id
        if isinstance(other, discord.Member):
            return self.member.id == other.id
        return False
