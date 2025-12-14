"""Bidding strategy predictor."""

from typing import Dict, List, Any, Optional
from models.player import Player
from models.team import Team
from core.auction_modeler import AuctionModeler
from core.bias_modeler import BiasModeler


class BiddingPredictor:
    """Predict bidding strategies for teams."""
    
    def __init__(self, auction_modeler: AuctionModeler, bias_modeler: BiasModeler):
        """Initialize predictor."""
        self.modeler = auction_modeler
        self.bias_modeler = bias_modeler
    
    def predict_team_bidding(
        self,
        player: Player,
        team: Team,
        demand_score: float
    ) -> Dict[str, Any]:
        """Predict how a team will bid for a player."""
        # Get bias score
        bias_score = self.bias_modeler.get_bias_score(player.name, team.name)
        
        # Predict behavior
        behavior = self.modeler.predict_bidding_behavior(
            player, team, demand_score, bias_score
        )
        
        # Predict price
        price_prediction = self.modeler.predict_price(
            player, team, demand_score, bias_score, competition_level=1
        )
        
        return {
            'team': team.name,
            'player': player.name,
            'behavior': behavior,
            'bias_score': bias_score,
            'price_prediction': price_prediction,
            'will_bid': demand_score > 5.0 or bias_score > 0.3
        }
    
    def predict_all_teams_bidding(
        self,
        player: Player,
        teams: Dict[str, Team],
        demand_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Predict bidding for all teams."""
        predictions = []
        
        for team_name, team in teams.items():
            demand_score = demand_scores.get(team_name, 0)
            prediction = self.predict_team_bidding(player, team, demand_score)
            predictions.append(prediction)
        
        # Sort by likelihood to bid
        predictions.sort(key=lambda x: (x['will_bid'], x['price_prediction']['fair_price_range'][0]), reverse=True)
        
        return predictions

