"""State manager for real-time auction state updates."""

from typing import Optional, List
from models.auction_state import AuctionState
from models.player import Player
from models.team import Team
import json
from pathlib import Path


class StateManager:
    """Manages auction state with real-time updates."""
    
    def __init__(self, auction_state: Optional[AuctionState] = None):
        """Initialize state manager."""
        self.state = auction_state or AuctionState()
    
    def sell_player(self, player_name: str, team_name: str, price: int, timestamp: Optional[str] = None):
        """Sell a player and update state immediately."""
        player = self.state.get_player(player_name)
        if not player:
            raise ValueError(f"Player {player_name} not found in available supply")
        
        if team_name not in self.state.teams:
            raise ValueError(f"Team {team_name} not found")
        
        team = self.state.teams[team_name]
        
        # Check if team can afford
        if team.purse_available < price:
            raise ValueError(f"Team {team_name} cannot afford {price}L (available: {team.purse_available}L)")
        
        # Check foreign slot if needed
        if player.country != "Indian" and team.available_foreign_slots <= 0:
            raise ValueError(f"Team {team_name} has no foreign slots available")
        
        # Check available slots
        if team.available_slots <= 0:
            raise ValueError(f"Team {team_name} has no slots available")
        
        # Record sale
        self.state.add_sold_player(player, team_name, price, timestamp)
    
    def update_team_purse(self, team_name: str, amount: int):
        """Update team purse (deduct amount)."""
        if team_name not in self.state.teams:
            raise ValueError(f"Team {team_name} not found")
        self.state.update_team_purse(team_name, amount)
    
    def remove_from_supply(self, player_name: str):
        """Remove player from available supply."""
        self.state.remove_from_supply(player_name)
    
    def get_player(self, player_name: str) -> Optional[Player]:
        """Get player by name."""
        return self.state.get_player(player_name)
    
    def get_team(self, team_name: str) -> Optional[Team]:
        """Get team by name."""
        return self.state.get_team(team_name)
    
    def get_available_players(self) -> List[Player]:
        """Get all available players."""
        return self.state.available_players
    
    def get_sold_players(self) -> List:
        """Get all sold players."""
        return self.state.sold_players
    
    def get_all_teams(self) -> dict:
        """Get all teams."""
        return self.state.teams
    
    def get_supply_count(self) -> int:
        """Get count of available players."""
        return self.state.get_supply_count()
    
    def export_state(self, file_path: str):
        """Export state to JSON file."""
        state_dict = self.state.to_dict()
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(state_dict, f, indent=2, ensure_ascii=False)
    
    def import_state(self, file_path: str):
        """Import state from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            state_dict = json.load(f)
        self.state = AuctionState.from_dict(state_dict)
    
    def reset_state(self, players: List[Player], teams: dict):
        """Reset state with new players and teams."""
        self.state = AuctionState()
        self.state.available_players = players
        self.state.teams = teams

