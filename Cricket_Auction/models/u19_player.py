"""U19 player model for tracking young talent."""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class U19Player:
    """U19 player model from authorized sources."""
    
    name: str
    country: str
    tournament: str  # e.g., "U19 World Cup 2024"
    year: int
    role: Optional[str] = None  # Batter, Bowler, All-rounder
    performance: Dict[str, Any] = field(default_factory=dict)
    
    # Link to main player database if they appear in supply
    linked_player_name: Optional[str] = None
    
    # Additional metadata
    source: str = ""  # Website source
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'country': self.country,
            'tournament': self.tournament,
            'year': self.year,
            'role': self.role,
            'performance': self.performance,
            'linked_player_name': self.linked_player_name,
            'source': self.source,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'U19Player':
        """Create from dictionary."""
        return cls(
            name=data['name'],
            country=data['country'],
            tournament=data['tournament'],
            year=data['year'],
            role=data.get('role'),
            performance=data.get('performance', {}),
            linked_player_name=data.get('linked_player_name'),
            source=data.get('source', ''),
            metadata=data.get('metadata', {})
        )

