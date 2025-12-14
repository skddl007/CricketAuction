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
        print(f"[TEAM_SELECTION] Getting recommendations for team: {team_name}")
        print(f"[TEAM_SELECTION] Filter group: {filter_group}")
        print(f"[TEAM_SELECTION] StateManager exists: {self.state_manager is not None}")
        print(f"[TEAM_SELECTION] Recommender exists: {self.recommender is not None}")
        print(f"[TEAM_SELECTION] PlayerGrouper exists: {self.player_grouper is not None}")
        
        team_name = normalize_team_name(team_name)
        print(f"[TEAM_SELECTION] Normalized team name: {team_name}")
        
        team = self.state_manager.get_team(team_name)
        print(f"[TEAM_SELECTION] Team found: {team is not None}")
        
        if not team:
            print(f"[TEAM_SELECTION] ERROR: Team {team_name} not found")
            return {'error': f"Team {team_name} not found"}
        
        print(f"[TEAM_SELECTION] Team details - Purse: {team.purse_available/100:.2f} Cr, Slots: {team.available_slots}")
        
        print("[TEAM_SELECTION] Getting available players...")
        available_players = self.state_manager.get_available_players()
        print(f"[TEAM_SELECTION] Available players count: {len(available_players)}")
        
        if not available_players:
            print("[TEAM_SELECTION] WARNING: No available players!")
            return {
                'team': team_name,
                'purse': team.purse_available / 100.0,
                'slots': team.available_slots,
                'groups': {'A': [], 'B': [], 'C': []},
                'formatted': f"No available players for {team_name}",
                'error': 'No available players'
            }
        
        print("[TEAM_SELECTION] Getting grouped recommendations...")
        groups = self.player_grouper.get_grouped_recommendations(team, available_players)
        print(f"[TEAM_SELECTION] Groups returned: {list(groups.keys())}")
        for group_name, group_data in groups.items():
            count = len(group_data) if isinstance(group_data, list) else 0
            print(f"[TEAM_SELECTION]   Group {group_name}: {count} recommendations")
        
        # Apply filters
        if filter_group:
            print(f"[TEAM_SELECTION] Applying group filter: {filter_group}")
            if filter_group.upper() in groups:
                groups = {filter_group.upper(): groups[filter_group.upper()]}
                print(f"[TEAM_SELECTION] Filtered to group {filter_group.upper()}: {len(groups[filter_group.upper()])} items")
            else:
                print(f"[TEAM_SELECTION] ERROR: Invalid group {filter_group}")
                return {'error': f"Invalid group: {filter_group}. Use A, B, or C"}
        
        # Filter by price if specified
        if filter_price_min or filter_price_max:
            print(f"[TEAM_SELECTION] Applying price filter: {filter_price_min} - {filter_price_max}")
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
                print(f"[TEAM_SELECTION] Group {group_name} after price filter: {len(filtered)} items")
        
        result = {
            'team': team_name,
            'purse': team.purse_available / 100.0,
            'slots': team.available_slots,
            'groups': groups,
            'formatted': self.player_grouper.format_grouped_recommendations(team, groups)
        }
        
        print(f"[TEAM_SELECTION] Returning result with {len(result)} keys")
        print(f"[TEAM_SELECTION] Total recommendations across all groups: {sum(len(g) if isinstance(g, list) else 0 for g in groups.values())}")
        
        return result
    
    def list_all_teams(self) -> List[str]:
        """List all available teams."""
        teams = self.state_manager.get_all_teams()
        return list(teams.keys())

