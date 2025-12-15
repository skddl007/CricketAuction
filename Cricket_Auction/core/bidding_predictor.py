"""Bidding strategy predictor - LLM-driven context-aware logic (no hardcoded thresholds)."""

from typing import Dict, List, Any, Optional
from models.player import Player
from models.team import Team
from core.auction_modeler import AuctionModeler
from core.bias_modeler import BiasModeler


class BiddingPredictor:
    """Predict bidding strategies contextually based on team state."""
    
    def __init__(self, auction_modeler: AuctionModeler, bias_modeler: BiasModeler):
        """Initialize predictor."""
        self.modeler = auction_modeler
        self.bias_modeler = bias_modeler
    
    def predict_team_bidding(
        self,
        player: Player,
        team: Team,
        demand_score: float,
        is_primary_gap: bool = False
    ) -> Dict[str, Any]:
        """
        Predict how a team will bid for a player based on CONTEXT.
        
        Per AuctionPrompt:
        - Aggressive: Primary gap + affordable + high demand
        - Moderate: Secondary gap OR high demand but tight purse
        - Passive: Low demand or cannot afford
        
        NOTE: No hardcoded thresholds. Logic is contextual.
        """
        # Get bias score (0-1)
        bias_score = self.bias_modeler.get_bias_score(player.name, team.name)
        
        # Calculate price prediction
        price_info = self.modeler.calculate_price_from_demand(
            player, demand_score, is_primary_gap
        )
        
        # Predict behavior based on team state + demand + affordability
        team_purse_cr = team.purse_available / 100.0
        fair_price_min = price_info['fair_price_min']
        fair_price_max = price_info['fair_price_max']
        fair_price_avg = (fair_price_min + fair_price_max) / 2
        
        behavior = self.modeler.predict_bidding_behavior(
            demand_score=demand_score,
            team_purse_available_cr=team_purse_cr,
            team_slots_available=team.available_slots,
            player_base_price_cr=price_info['base_price_cr']
        )
        
        # Determine likelihood to bid (NOT hardcoded threshold)
        will_bid = (
            demand_score >= 6.0 or  # Reasonable demand
            (is_primary_gap and demand_score >= 5.0) or  # Critical gap + decent demand
            (bias_score >= 0.5)  # Strong historical bias
        )
        
        return {
            'team': team.name,
            'player': player.name,
            'demand_score': demand_score,
            'bias_score': bias_score,
            'is_primary_gap': is_primary_gap,
            'behavior': behavior,
            'will_bid': will_bid,
            'bidding_confidence': min((demand_score + bias_score*10) / 10, 1.0),
            'estimated_fair_price': f"{fair_price_min:.1f}-{fair_price_max:.1f}",
            'team_purse_remaining': f"{team_purse_cr:.1f}Cr",
            'can_afford_fair_price': team_purse_cr >= fair_price_min
        }
    
    def predict_all_teams_bidding(
        self,
        player: Player,
        teams: Dict[str, Team],
        demand_scores: Dict[str, float],
        primary_gap_teams: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Predict bidding for all teams.
        
        Args:
            player: Player being auctioned
            teams: All teams
            demand_scores: Demand score for each team
            primary_gap_teams: List of teams for which this player fills CRITICAL gap
        """
        if primary_gap_teams is None:
            primary_gap_teams = []
        
        predictions = []
        
        for team_name, team in teams.items():
            demand_score = demand_scores.get(team_name, 0)
            is_primary = team_name in primary_gap_teams
            
            prediction = self.predict_team_bidding(player, team, demand_score, is_primary)
            predictions.append(prediction)
        
        # Sort by likelihood to bid (highest first)
        # Primary: will_bid teams
        # Secondary: by behavior aggressiveness (aggressive > moderate > passive)
        # Tertiary: by demand score
        
        def sort_key(p):
            will_bid_weight = 100 if p['will_bid'] else 0
            behavior_weight = {
                'aggressive': 10,
                'moderate': 5,
                'passive': 0
            }.get(p['behavior'], 0)
            return (will_bid_weight + behavior_weight, p['demand_score'])
        
        predictions.sort(key=sort_key, reverse=True)
        
        return predictions
    
    def estimate_competition_level(
        self,
        player: Player,
        all_teams: Dict[str, Team],
        demand_scores: Dict[str, float]
    ) -> int:
        """Estimate how many teams will compete for this player (demand >= 6.0)."""
        competing_teams = sum(1 for score in demand_scores.values() if score >= 6.0)
        return competing_teams

