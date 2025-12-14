"""Live bid-by-bid mode handler."""

from typing import Dict, List, Any
from core.state_manager import StateManager
from core.recommender import Recommender
from core.player_grouper import PlayerGrouper
from utils import parse_price_string, normalize_team_name


class LiveBidHandler:
    """Handle live bid-by-bid auction tracking."""
    
    def __init__(
        self,
        state_manager: StateManager,
        recommender: Recommender,
        player_grouper: PlayerGrouper
    ):
        """Initialize live bid handler."""
        self.state_manager = state_manager
        self.recommender = recommender
        self.player_grouper = player_grouper
        self.bid_count = 0
        self.previous_recommendations = {}
    
    def process_bid(self, player_name: str, team_name: str, price: str) -> Dict[str, Any]:
        """Process a bid and return updated recommendations."""
        self.bid_count += 1
        
        # Parse price
        price_lakhs = parse_price_string(price)
        if not price_lakhs:
            return {'error': f"Invalid price: {price}"}
        
        team_name = normalize_team_name(team_name)
        
        # Record sale
        try:
            self.state_manager.sell_player(player_name, team_name, price_lakhs)
        except Exception as e:
            return {'error': str(e)}
        
        # Get updated recommendations for all teams
        updated_recommendations = self.get_all_teams_recommendations()
        
        result = {
            'bid_number': self.bid_count,
            'player': player_name,
            'team': team_name,
            'price': price,
            'recommendations': updated_recommendations
        }
        
        return result
    
    def get_all_teams_recommendations(self) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
        """Get grouped recommendations for all teams."""
        teams = self.state_manager.get_all_teams()
        available_players = self.state_manager.get_available_players()
        
        all_recommendations = {}
        
        for team_name, team in teams.items():
            groups = self.player_grouper.get_grouped_recommendations(team, available_players, limit_per_group=3)
            all_recommendations[team_name] = groups
        
        return all_recommendations
    
    def format_bid_result(self, result: Dict[str, Any]) -> str:
        """Format bid result for display."""
        if result.get('error'):
            return f"Error: {result['error']}"
        
        lines = [
            f"=== Live Auction - Bid #{result['bid_number']} ===",
            f"Player: {result['player']} → Team: {result['team']} at {result['price']}",
            ""
        ]
        
        recommendations = result.get('recommendations', {})
        
        for team_name, groups in recommendations.items():
            lines.append(f"{team_name}:")
            
            if groups.get('A'):
                lines.append("  Group A:")
                for rec in groups['A'][:3]:
                    player_name = rec.get('player_name', 'Unknown')
                    demand = rec.get('overall_demand_score', 0)
                    lines.append(f"    - {player_name}: Demand {demand:.1f}/10")
            
            if groups.get('B'):
                lines.append("  Group B:")
                for rec in groups['B'][:3]:
                    player_name = rec.get('player_name', 'Unknown')
                    demand = rec.get('overall_demand_score', 0)
                    lines.append(f"    - {player_name}: Demand {demand:.1f}/10")
            
            lines.append("")
        
        return "\n".join(lines)

