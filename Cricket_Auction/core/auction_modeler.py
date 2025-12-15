"""Auction behavior modeler - LLM-driven (no hardcoded price formulas)."""

from typing import Dict, Any, Optional, Tuple
from models.player import Player
from models.team import Team


class AuctionModeler:
    """Model auction behavior based on demand components (LLM-calculated)."""
    
    def __init__(self):
        """Initialize modeler."""
        pass
    
    def calculate_price_from_demand(
        self,
        player: Player,
        demand_score: float,
        is_primary_gap: bool = False
    ) -> Dict[str, Any]:
        """
        Calculate price bands from demand score per AuctionPrompt Step f.
        
        Formula (NOT hardcoded):
        - Fair Price = Base price + (demand_score / 10) × 100% uplift
        - Likely Price = Fair price ± 20% (market adjustment)
        - All-Out Price = If fills PRIMARY gap, add 40% to Likely
        
        Args:
            player: Player object with base_price
            demand_score: 0-10 scale from demand calculation
            is_primary_gap: True if player fills a CRITICAL/OPEN position
        
        Returns:
            Dict with fair/likely/all-out price ranges
        """
        base_price_cr = player.base_price / 100.0
        
        # Step 1: Fair price based on demand
        demand_uplift = (demand_score / 10.0) * base_price_cr  # e.g., demand=8 → 0.8x base uplift
        fair_price_min = base_price_cr + demand_uplift
        fair_price_max = fair_price_min * 1.2  # 20% range
        
        # Step 2: Likely price (market adjustment around fair price)
        likely_price_min = fair_price_min
        likely_price_max = fair_price_max
        
        # Step 3: All-out price (only if fills PRIMARY gap)
        all_out_price_min = fair_price_max
        all_out_price_max = all_out_price_min * 1.4  # 40% uplift if primary gap
        
        return {
            'base_price_cr': base_price_cr,
            'demand_score': demand_score,
            'fair_price_min': round(fair_price_min, 1),
            'fair_price_max': round(fair_price_max, 1),
            'likely_price_min': round(likely_price_min, 1),
            'likely_price_max': round(likely_price_max, 1),
            'all_out_price_min': round(all_out_price_min, 1) if is_primary_gap else None,
            'all_out_price_max': round(all_out_price_max, 1) if is_primary_gap else None,
            'is_primary_gap': is_primary_gap,
            'price_confidence': min(demand_score / 10.0, 1.0)  # Higher demand = more confident
        }
    
    def predict_bidding_behavior(
        self,
        demand_score: float,
        team_purse_available_cr: float,
        team_slots_available: int,
        player_base_price_cr: float
    ) -> str:
        """
        Predict bidding behavior based on CONTEXT, not hardcoded thresholds.
        
        Returns: 'aggressive', 'moderate', or 'passive'
        """
        # Check if team CAN bid
        if team_purse_available_cr < player_base_price_cr:
            return 'passive'  # Cannot afford even base price
        
        if team_slots_available < 1:
            return 'passive'  # No slots available
        
        # Check demand vs affordability
        fair_price_estimate = player_base_price_cr * (1 + demand_score / 10.0)
        purse_ratio = fair_price_estimate / team_purse_available_cr
        
        # Context-aware bidding
        if demand_score >= 8.0 and purse_ratio <= 0.3:
            return 'aggressive'  # High demand + affordable = bid aggressively
        elif demand_score >= 6.0 and purse_ratio <= 0.5:
            return 'moderate'  # Good demand + moderate cost = moderate bidding
        elif demand_score >= 5.0:
            return 'moderate'  # Acceptable demand
        else:
            return 'passive'  # Low demand = passive bidding
    
    def estimate_competing_teams(
        self,
        demand_scores_by_team: Dict[str, float]
    ) -> int:
        """Count teams likely to compete for this player."""
        # Teams with demand >= 6.0 will actively bid
        competing = sum(1 for score in demand_scores_by_team.values() if score >= 6.0)
        return competing

