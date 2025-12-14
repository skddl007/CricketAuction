"""Auction behavior modeler with bias factor integration."""

from typing import Dict, Any, Optional, Tuple
from models.player import Player
from models.team import Team


class AuctionModeler:
    """Model auction behavior and predict prices."""
    
    def __init__(self):
        """Initialize modeler."""
        pass
    
    def predict_price(
        self,
        player: Player,
        team: Team,
        demand_score: float,
        bias_score: float = 0.0,
        competition_level: int = 1
    ) -> Dict[str, Any]:
        """Predict likely auction price."""
        base_price_cr = player.base_price / 100.0
        
        # Base prediction factors
        demand_factor = demand_score / 10.0  # 0-1
        bias_factor = bias_score  # 0-1
        competition_factor = min(competition_level / 5.0, 1.0)  # 0-1
        
        # Calculate price multiplier
        multiplier = 1.0 + (demand_factor * 2.0) + (bias_factor * 0.5) + (competition_factor * 0.3)
        
        # Predict fair price
        fair_price_min = base_price_cr * multiplier
        fair_price_max = fair_price_min * 1.3
        
        # Predict all-out price (if fills primary gap)
        all_out_price_min = fair_price_max
        all_out_price_max = all_out_price_min * 1.5
        
        # Likely price (most probable)
        likely_price_min = (fair_price_min + fair_price_max) / 2
        likely_price_max = likely_price_max
        
        return {
            'base_price_cr': base_price_cr,
            'fair_price_range': (fair_price_min, fair_price_max),
            'likely_price_range': (likely_price_min, likely_price_max),
            'all_out_price_range': (all_out_price_min, all_out_price_max),
            'confidence': min(demand_factor + bias_factor, 1.0)
        }
    
    def predict_bidding_behavior(
        self,
        player: Player,
        team: Team,
        demand_score: float,
        bias_score: float = 0.0
    ) -> str:
        """Predict if team will bid aggressively or passively."""
        total_score = demand_score + (bias_score * 10)
        
        if total_score >= 8.0:
            return "aggressive"
        elif total_score >= 6.0:
            return "moderate"
        else:
            return "passive"
    
    def estimate_competition_level(
        self,
        player: Player,
        all_teams: Dict[str, Team],
        demand_scores: Dict[str, float]
    ) -> int:
        """Estimate how many teams will compete for this player."""
        # Count teams with demand score > 6
        competing_teams = sum(1 for score in demand_scores.values() if score > 6.0)
        return competing_teams

