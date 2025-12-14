"""Auction state model for real-time state management."""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from .player import Player
from .team import Team


@dataclass
class SoldPlayer:
    """Record of a sold player."""
    player: Player
    team: str
    price: int  # in lakhs
    timestamp: Optional[str] = None


@dataclass
class AuctionState:
    """Real-time auction state management."""
    
    available_players: List[Player] = field(default_factory=list)
    sold_players: List[SoldPlayer] = field(default_factory=list)
    teams: Dict[str, Team] = field(default_factory=dict)
    
    def add_sold_player(self, player: Player, team_name: str, price: int, timestamp: Optional[str] = None):
        """Record a player sale and update state."""
        # Remove from available
        self.available_players = [p for p in self.available_players if p.name != player.name]
        
        # Add to sold
        sold = SoldPlayer(player=player, team=team_name, price=price, timestamp=timestamp)
        self.sold_players.append(sold)
        
        # Update team
        if team_name in self.teams:
            self.teams[team_name].add_bought_player(player, price)
    
    def remove_from_supply(self, player_name: str):
        """Remove player from available supply."""
        self.available_players = [p for p in self.available_players if p.name != player_name]
    
    def update_team_purse(self, team_name: str, amount: int):
        """Update team purse (deduct amount)."""
        if team_name in self.teams:
            self.teams[team_name].purse_available -= amount
    
    def get_player(self, player_name: str) -> Optional[Player]:
        """Get player by name from available or sold."""
        # Check available first
        for player in self.available_players:
            if player.name == player_name:
                return player
        
        # Check sold
        for sold in self.sold_players:
            if sold.player.name == player_name:
                return sold.player
        
        return None
    
    def get_team(self, team_name: str) -> Optional[Team]:
        """Get team by name."""
        return self.teams.get(team_name)
    
    def get_supply_count(self) -> int:
        """Get count of available players."""
        return len(self.available_players)
    
    def to_dict(self) -> Dict:
        """Export state to dictionary for persistence."""
        return {
            'available_players': [p.to_dict() for p in self.available_players],
            'sold_players': [
                {
                    'player': sold.player.to_dict(),
                    'team': sold.team,
                    'price': sold.price,
                    'timestamp': sold.timestamp
                }
                for sold in self.sold_players
            ],
            'teams': {name: team.to_dict() for name, team in self.teams.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AuctionState':
        """Import state from dictionary."""
        from .player import Player as PlayerModel
        from .team import Team as TeamModel
        
        # Reconstruct players
        available_players = [PlayerModel.from_dict(p) for p in data.get('available_players', [])]
        sold_players_data = data.get('sold_players', [])
        
        # Create player lookup
        all_players = {p.name: p for p in available_players}
        
        # Reconstruct sold players
        sold_players = []
        for sold_data in sold_players_data:
            player_data = sold_data['player']
            if player_data['name'] not in all_players:
                all_players[player_data['name']] = PlayerModel.from_dict(player_data)
            player = all_players[player_data['name']]
            sold = SoldPlayer(
                player=player,
                team=sold_data['team'],
                price=sold_data['price'],
                timestamp=sold_data.get('timestamp')
            )
            sold_players.append(sold)
        
        # Reconstruct teams
        teams = {}
        for team_name, team_data in data.get('teams', {}).items():
            teams[team_name] = TeamModel.from_dict(team_data, players=list(all_players.values()))
        
        state = cls(
            available_players=available_players,
            sold_players=sold_players,
            teams=teams
        )
        
        return state

