"""Team model with home ground conditions and squad management."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .player import Player


@dataclass
class Team:
    """Team model with players, purse, and home ground conditions."""
    
    name: str
    home_ground: str
    ground_condition: str  # e.g., "spin-friendly", "pace-friendly", "balanced"
    purse_available: int  # in lakhs
    total_slots: int
    foreign_slots: int
    players_retained: int
    foreign_players_retained: int
    retention_spends: int  # in lakhs
    
    # Squad management
    retained_players: List[Player] = field(default_factory=list)
    bought_players: List[Player] = field(default_factory=list)
    
    # Home ground analysis
    ground_requirements: List[str] = field(default_factory=list)  # e.g., ["needs spinners"]
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_players(self) -> int:
        """Total players in squad."""
        return len(self.retained_players) + len(self.bought_players)
    
    @property
    def total_foreign_players(self) -> int:
        """Total foreign players in squad."""
        return (
            sum(1 for p in self.retained_players if p.country != "Indian") +
            sum(1 for p in self.bought_players if p.country != "Indian")
        )
    
    @property
    def available_slots(self) -> int:
        """Available slots remaining."""
        return self.total_slots - self.total_players
    
    @property
    def available_foreign_slots(self) -> int:
        """Available foreign slots remaining."""
        return self.foreign_slots - self.total_foreign_players
    
    @property
    def current_purse(self) -> int:
        """Current purse after all purchases."""
        return self.purse_available
    
    def add_bought_player(self, player: Player, price: int):
        """Add a bought player and update purse."""
        self.bought_players.append(player)
        self.purse_available -= price
    
    def get_all_players(self) -> List[Player]:
        """Get all players (retained + bought)."""
        return self.retained_players + self.bought_players
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert team to dictionary."""
        return {
            'name': self.name,
            'home_ground': self.home_ground,
            'ground_condition': self.ground_condition,
            'purse_available': self.purse_available,
            'total_slots': self.total_slots,
            'foreign_slots': self.foreign_slots,
            'players_retained': self.players_retained,
            'foreign_players_retained': self.foreign_players_retained,
            'retention_spends': self.retention_spends,
            'retained_players': [p.name for p in self.retained_players],
            'bought_players': [p.name for p in self.bought_players],
            'ground_requirements': self.ground_requirements,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], players: Optional[List[Player]] = None) -> 'Team':
        """Create team from dictionary."""
        team = cls(
            name=data['name'],
            home_ground=data['home_ground'],
            ground_condition=data['ground_condition'],
            purse_available=data['purse_available'],
            total_slots=data['total_slots'],
            foreign_slots=data['foreign_slots'],
            players_retained=data['players_retained'],
            foreign_players_retained=data['foreign_players_retained'],
            retention_spends=data['retention_spends'],
            ground_requirements=data.get('ground_requirements', []),
            metadata=data.get('metadata', {})
        )
        
        # Link players if provided
        if players:
            player_dict = {p.name: p for p in players}
            team.retained_players = [player_dict[name] for name in data.get('retained_players', []) if name in player_dict]
            team.bought_players = [player_dict[name] for name in data.get('bought_players', []) if name in player_dict]
        
        return team

