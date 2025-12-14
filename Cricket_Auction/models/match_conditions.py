"""Match conditions model for tracking pitch, weather, and match context."""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum


class PitchCondition(Enum):
    """Pitch condition types."""
    SPIN_FRIENDLY = "spin_friendly"
    PACE_FRIENDLY = "pace_friendly"
    BATTER_FRIENDLY = "batter_friendly"
    BALANCED = "balanced"
    UNKNOWN = "unknown"


@dataclass
class MatchConditions:
    """Track match conditions and context."""
    
    match_id: str
    pitch_condition: Optional[PitchCondition] = None
    weather: Optional[str] = None
    wickets_fallen_at_entry: int = 0
    score_at_entry: Optional[int] = None
    required_rate: Optional[float] = None
    match_type: Optional[str] = None  # e.g., "league", "playoff", "final"
    venue: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        """Initialize metadata if not provided."""
        if self.metadata is None:
            self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'match_id': self.match_id,
            'pitch_condition': self.pitch_condition.value if self.pitch_condition else None,
            'weather': self.weather,
            'wickets_fallen_at_entry': self.wickets_fallen_at_entry,
            'score_at_entry': self.score_at_entry,
            'required_rate': self.required_rate,
            'match_type': self.match_type,
            'venue': self.venue,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MatchConditions':
        """Create from dictionary."""
        pitch_condition = None
        if data.get('pitch_condition'):
            pitch_condition = PitchCondition(data['pitch_condition'])
        
        return cls(
            match_id=data['match_id'],
            pitch_condition=pitch_condition,
            weather=data.get('weather'),
            wickets_fallen_at_entry=data.get('wickets_fallen_at_entry', 0),
            score_at_entry=data.get('score_at_entry'),
            required_rate=data.get('required_rate'),
            match_type=data.get('match_type'),
            venue=data.get('venue'),
            metadata=data.get('metadata', {})
        )

