import random

class FairnessEngine:
    def determine_winner(self, player_a, player_b):
        """
        Determines the winner based on NFT status, Pepe rules, and Loot bonuses.
        """
        # 1. NFT vs Pepe Rules
        # "A NFT ALWAYS BEATS Pepes"
        if not player_a.is_pepe and player_b.is_pepe:
            return player_a
        if player_a.is_pepe and not player_b.is_pepe:
            return player_b
            
        # 2. Pepe vs Pepe Rules
        # "Pepe Bro ALWAYS BEATS Pepe Jeet"
        if player_a.is_pepe and player_b.is_pepe:
            type_a = player_a.current_nft.get('pepe_type')
            type_b = player_b.current_nft.get('pepe_type')
            
            if type_a == "BRO" and type_b == "JEET":
                return player_a
            if type_a == "JEET" and type_b == "BRO":
                return player_b
            # If same type, fall through to RNG/Loot
            
        # 3. Standard Calculation (NFT vs NFT OR Same-Type Pepe vs Pepe)
        # Base Score (Inverse Rarity Rank? Or just random base strength?)
        # Assuming lower rank is better (1 is #1). So Score = 10000 - Rank
        
        score_a = self._calculate_score(player_a)
        score_b = self._calculate_score(player_b)
        
        # Add Loot Bonuses
        if player_a.current_loot:
            score_a += player_a.current_loot['bonus']
        if player_b.current_loot:
            score_b += player_b.current_loot['bonus']
            
        # Determine Winner based on Score
        # Add some RNG variance? "Upset potential"
        # Let's say Score is the weight.
        
        total_score = score_a + score_b
        if total_score == 0: return random.choice([player_a, player_b])
        
        chance_a = score_a / total_score
        
        if random.random() < chance_a:
            return player_a
        else:
            return player_b

    def _calculate_score(self, player):
        if player.is_pepe:
            return 500 # Base score for Pepe
        
        # NFT Score
        rank = player.current_nft.get('rarity_rank', 5000)
        # Invert rank: Rank 1 = 10000 pts, Rank 5000 = 5000 pts
        # Cap at 10000
        return max(1000, 11000 - rank)
