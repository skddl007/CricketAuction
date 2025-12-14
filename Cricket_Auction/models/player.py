"""Player model with comprehensive tagging and advanced metrics."""

from dataclasses import dataclass, field
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class PrimaryRole(Enum):
    """Primary role of the player."""
    BATTER = "Batter"
    BOWLER = "Bowler"
    BAT_AR = "BatAR"  # Bat-dominant all-rounder
    BOWL_AR = "BowlAR"  # Bowl-dominant all-rounder
    SPINNER = "Spinner"
    PACER = "Pacer"


class BattingRole(Enum):
    """Batting role and position."""
    OPENER = "Opener"
    MIDDLE_ORDER = "MiddleOrder"
    FINISHER = "Finisher"


class BowlingRole(Enum):
    """Bowling role types."""
    PACER = "Pacer"
    WRIST_SPINNER = "WristSpinner"
    FINGER_SPINNER = "FingerSpinner"
    LEFT_ARM_SPINNER = "LeftArmSpinner"
    LEG_SPIN = "LegSpin"
    OFF_SPIN = "OffSpin"
    MYSTERY_SPINNER = "MysterySpinner"


class Speciality(Enum):
    """Player speciality."""
    WK_BAT = "WKBat"
    PP_BOWLER = "PPBowler"
    MO_BOWLER = "MOBowler"
    DEATH_BOWLER = "DeathBowler"


class Quality(Enum):
    """Player quality tier."""
    A = "A"
    B = "B"


@dataclass
class PhaseMetrics:
    """Phase-wise metrics for a player."""
    powerplay: Optional[Dict[str, float]] = None  # {efscore, winp, raa}
    middle_overs: Optional[Dict[str, float]] = None
    death: Optional[Dict[str, float]] = None
    
    def __post_init__(self):
        """Initialize metrics if not provided."""
        if self.powerplay is None:
            self.powerplay = {}
        if self.middle_overs is None:
            self.middle_overs = {}
        if self.death is None:
            self.death = {}


@dataclass
class Player:
    """Comprehensive player model with advanced metrics and conditions tracking."""
    
    name: str
    base_price: int  # in lakhs
    country: str
    batting_hand: Optional[str] = None  # LHB or RHB
    bowling_style: Optional[str] = None
    
    # Core attributes
    primary_role: Optional[PrimaryRole] = None
    batting_role: Optional[BattingRole] = None
    bowling_role: Optional[BowlingRole] = None
    speciality: Optional[Speciality] = None
    quality: Optional[Quality] = None
    
    # Utilization tags
    bat_utilization: List[str] = field(default_factory=list)  # Floater, Anchor, PlaysSpinWell, etc.
    bowl_utilization: List[str] = field(default_factory=list)  # CanBowl4Overs, CanBowl2Overs, etc.
    
    # Experience and leagues
    international_leagues: List[Tuple[str, str, int]] = field(default_factory=list)  # (league, team, year)
    ipl_experience: List[Tuple[int, str]] = field(default_factory=list)  # (year, team)
    scouting: List[str] = field(default_factory=list)  # Teams that called for trials
    
    # Performance data
    smat_performance: List[Dict[str, Any]] = field(default_factory=list)  # Outstanding knocks/spells
    
    # Advanced metrics (phase-wise)
    advanced_metrics: Optional[PhaseMetrics] = None
    
    # Match conditions tracking
    match_conditions: List[Tuple[str, Dict[str, Any]]] = field(default_factory=list)  # (match_id, conditions, performance)
    performance_by_conditions: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # Conditions -> performance stats
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_match_condition(self, match_id: str, conditions: Dict[str, Any], performance: Dict[str, Any]):
        """Add match condition and performance data."""
        self.match_conditions.append((match_id, {**conditions, 'performance': performance}))
        
        # Update performance by conditions
        wickets_key = f"wickets_{conditions.get('wickets_fallen_at_entry', 0)}"
        if wickets_key not in self.performance_by_conditions:
            self.performance_by_conditions[wickets_key] = {
                'matches': 0,
                'runs': 0,
                'wickets': 0,
                'avg_runs': 0.0,
                'avg_wickets': 0.0
            }
        
        stats = self.performance_by_conditions[wickets_key]
        stats['matches'] += 1
        stats['runs'] += performance.get('runs', 0)
        stats['wickets'] += performance.get('wickets', 0)
        stats['avg_runs'] = stats['runs'] / stats['matches']
        stats['avg_wickets'] = stats['wickets'] / stats['matches']
    
    def get_conditions_balance_score(self) -> float:
        """Calculate how balanced the player is across different conditions."""
        if not self.performance_by_conditions:
            return 0.0
        
        # Calculate variance in performance across conditions
        # Lower variance = more balanced
        performances = []
        for condition_stats in self.performance_by_conditions.values():
            if condition_stats['matches'] > 0:
                # Combine runs and wickets into a single performance metric
                perf = condition_stats['avg_runs'] + (condition_stats['avg_wickets'] * 20)
                performances.append(perf)
        
        if len(performances) < 2:
            return 0.5  # Not enough data
        
        mean_perf = sum(performances) / len(performances)
        variance = sum((p - mean_perf) ** 2 for p in performances) / len(performances)
        
        # Normalize to 0-1 scale (inverse variance, higher = more balanced)
        max_variance = 1000  # Arbitrary max
        balance_score = 1.0 - min(variance / max_variance, 1.0)
        return balance_score
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary."""
        return {
            'name': self.name,
            'base_price': self.base_price,
            'country': self.country,
            'batting_hand': self.batting_hand,
            'bowling_style': self.bowling_style,
            'primary_role': self.primary_role.value if self.primary_role else None,
            'batting_role': self.batting_role.value if self.batting_role else None,
            'bowling_role': self.bowling_role.value if self.bowling_role else None,
            'speciality': self.speciality.value if self.speciality else None,
            'quality': self.quality.value if self.quality else None,
            'bat_utilization': self.bat_utilization,
            'bowl_utilization': self.bowl_utilization,
            'international_leagues': self.international_leagues,
            'ipl_experience': self.ipl_experience,
            'scouting': self.scouting,
            'smat_performance': self.smat_performance,
            'advanced_metrics': {
                'powerplay': self.advanced_metrics.powerplay if self.advanced_metrics else None,
                'middle_overs': self.advanced_metrics.middle_overs if self.advanced_metrics else None,
                'death': self.advanced_metrics.death if self.advanced_metrics else None
            } if self.advanced_metrics else None,
            'match_conditions': self.match_conditions,
            'performance_by_conditions': self.performance_by_conditions,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Player':
        """Create player from dictionary."""
        player = cls(
            name=data['name'],
            base_price=data['base_price'],
            country=data['country'],
            batting_hand=data.get('batting_hand'),
            bowling_style=data.get('bowling_style'),
            bat_utilization=data.get('bat_utilization', []),
            bowl_utilization=data.get('bowl_utilization', []),
            international_leagues=[tuple(x) for x in data.get('international_leagues', [])],
            ipl_experience=[tuple(x) for x in data.get('ipl_experience', [])],
            scouting=data.get('scouting', []),
            smat_performance=data.get('smat_performance', []),
            match_conditions=[tuple(x) for x in data.get('match_conditions', [])],
            performance_by_conditions=data.get('performance_by_conditions', {}),
            metadata=data.get('metadata', {})
        )
        
        # Set enums
        if data.get('primary_role'):
            player.primary_role = PrimaryRole(data['primary_role'])
        if data.get('batting_role'):
            player.batting_role = BattingRole(data['batting_role'])
        if data.get('bowling_role'):
            player.bowling_role = BowlingRole(data['bowling_role'])
        if data.get('speciality'):
            player.speciality = Speciality(data['speciality'])
        if data.get('quality'):
            player.quality = Quality(data['quality'])
        
        # Set advanced metrics
        if data.get('advanced_metrics'):
            metrics = PhaseMetrics()
            metrics.powerplay = data['advanced_metrics'].get('powerplay')
            metrics.middle_overs = data['advanced_metrics'].get('middle_overs')
            metrics.death = data['advanced_metrics'].get('death')
            player.advanced_metrics = metrics
        
        return player

