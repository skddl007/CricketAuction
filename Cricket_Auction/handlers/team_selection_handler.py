"""Team selection mode handler."""

from typing import Dict, List, Any, Optional
from models.team import Team
from core.state_manager import StateManager
from core.recommender import Recommender
from core.player_grouper import PlayerGrouper
from utils import normalize_team_name


class TeamSelectionHandler:
    """Handle team selection mode."""
    
    def __init__(
        self,
        state_manager: StateManager,
        recommender: Recommender,
        player_grouper: PlayerGrouper
    ):
        """Initialize handler."""
        self.state_manager = state_manager
        self.recommender = recommender
        self.player_grouper = player_grouper
    
    def get_team_recommendations(
        self,
        team_name: str,
        filter_group: Optional[str] = None,
        filter_price_min: Optional[float] = None,
        filter_price_max: Optional[float] = None
    ) -> Dict[str, Any]:
        """Get recommendations for a team."""
        team_name = normalize_team_name(team_name)
        team = self.state_manager.get_team(team_name)
        
        if not team:
            return {'error': f"Team {team_name} not found"}
        
        available_players = self.state_manager.get_available_players()
        groups = self.player_grouper.get_grouped_recommendations(team, available_players)
        
        # Apply filters
        if filter_group:
            if filter_group.upper() in groups:
                groups = {filter_group.upper(): groups[filter_group.upper()]}
            else:
                return {'error': f"Invalid group: {filter_group}. Use A, B, or C"}
        
        # Filter by price if specified
        if filter_price_min or filter_price_max:
            for group_name in groups:
                filtered = []
                for rec in groups[group_name]:
                    price_str = rec.get('fair_price_range', '0-0')
                    # Parse price range
                    try:
                        parts = price_str.split('-')
                        price_min = float(parts[0]) if parts else 0
                        price_max = float(parts[1]) if len(parts) > 1 else price_min
                        
                        if filter_price_min and price_max < filter_price_min:
                            continue
                        if filter_price_max and price_min > filter_price_max:
                            continue
                        
                        filtered.append(rec)
                    except:
                        filtered.append(rec)
                groups[group_name] = filtered
        
        return {
            'team': team_name,
            'purse': team.purse_available / 100.0,
            'slots': team.available_slots,
            'groups': groups,
            'formatted': self.player_grouper.format_grouped_recommendations(team, groups)
        }
    
    def list_all_teams(self) -> List[str]:
        """List all available teams."""
        teams = self.state_manager.get_all_teams()
        return list(teams.keys())

