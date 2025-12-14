"""Match conditions analyzer to track performance by wickets/conditions."""

from typing import Dict, List, Any, Optional
from models.player import Player
from models.match_conditions import MatchConditions, PitchCondition
from scrapers.cricsheet_fetcher import CricsheetFetcher


class ConditionsAnalyzer:
    """Analyze player performance by match conditions."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def extract_match_conditions(self, match_data: Dict[str, Any]) -> MatchConditions:
        """Extract match conditions from cricsheet match data."""
        meta = match_data.get('meta', {})
        
        # Extract basic info
        match_id = meta.get('match_id', '')
        venue = meta.get('venue', '')
        match_type = meta.get('event', '')
        
        # Try to infer pitch condition from venue (simplified)
        pitch_condition = self._infer_pitch_condition(venue)
        
        conditions = MatchConditions(
            match_id=match_id,
            pitch_condition=pitch_condition,
            venue=venue,
            match_type=match_type,
            metadata=meta
        )
        
        return conditions
    
    def _infer_pitch_condition(self, venue: str) -> PitchCondition:
        """Infer pitch condition from venue name."""
        venue_lower = venue.lower()
        
        # Known spin-friendly venues
        spin_venues = ['chepauk', 'chennai', 'eden', 'kolkata', 'jaipur']
        if any(sv in venue_lower for sv in spin_venues):
            return PitchCondition.SPIN_FRIENDLY
        
        # Known pace-friendly venues
        pace_venues = ['wankhede', 'mumbai', 'ahmedabad', 'mohali', 'chinnaswamy', 'bangalore']
        if any(pv in venue_lower for pv in pace_venues):
            return PitchCondition.PACE_FRIENDLY
        
        # Known batting-friendly venues
        batting_venues = ['chinnaswamy', 'bangalore']
        if any(bv in venue_lower for bv in batting_venues):
            return PitchCondition.BATTER_FRIENDLY
        
        return PitchCondition.BALANCED
    
    def analyze_player_conditions(self, player: Player, match_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze player performance across different conditions."""
        conditions_stats = {
            'wickets_0_2': {'matches': 0, 'runs': 0, 'wickets': 0, 'avg_runs': 0.0, 'avg_wickets': 0.0},
            'wickets_3_5': {'matches': 0, 'runs': 0, 'wickets': 0, 'avg_runs': 0.0, 'avg_wickets': 0.0},
            'wickets_6_plus': {'matches': 0, 'runs': 0, 'wickets': 0, 'avg_runs': 0.0, 'avg_wickets': 0.0},
            'powerplay': {'matches': 0, 'runs': 0, 'wickets': 0},
            'middle_overs': {'matches': 0, 'runs': 0, 'wickets': 0},
            'death': {'matches': 0, 'runs': 0, 'wickets': 0}
        }
        
        for match in match_data:
            performances = match.get('performances', [])
            match_conditions = self.extract_match_conditions(match.get('match_data', {}))
            
            for perf in performances:
                wickets_at_entry = perf.get('wickets_fallen', 0)
                
                # Categorize by wickets
                if wickets_at_entry <= 2:
                    key = 'wickets_0_2'
                elif wickets_at_entry <= 5:
                    key = 'wickets_3_5'
                else:
                    key = 'wickets_6_plus'
                
                # Update stats
                if key not in conditions_stats:
                    conditions_stats[key] = {'matches': 0, 'runs': 0, 'wickets': 0, 'avg_runs': 0.0, 'avg_wickets': 0.0}
                
                conditions_stats[key]['runs'] += perf.get('runs', 0)
                conditions_stats[key]['wickets'] += perf.get('wicket', 0) or 0
                
                # Phase stats
                phase = perf.get('phase', '')
                if phase in conditions_stats:
                    conditions_stats[phase]['runs'] += perf.get('runs', 0)
                    conditions_stats[phase]['wickets'] += perf.get('wicket', 0) or 0
        
        # Calculate averages
        for key in ['wickets_0_2', 'wickets_3_5', 'wickets_6_plus']:
            if conditions_stats[key]['matches'] > 0:
                conditions_stats[key]['avg_runs'] = conditions_stats[key]['runs'] / conditions_stats[key]['matches']
                conditions_stats[key]['avg_wickets'] = conditions_stats[key]['wickets'] / conditions_stats[key]['matches']
        
        return conditions_stats
    
    def update_player_conditions(self, player: Player, match_data: List[Dict[str, Any]]):
        """Update player's conditions performance data."""
        conditions_stats = self.analyze_player_conditions(player, match_data)
        
        # Store in player's performance_by_conditions
        player.performance_by_conditions = conditions_stats
        
        # Add match conditions to player
        for match in match_data:
            match_conditions = self.extract_match_conditions(match.get('match_data', {}))
            
            # Calculate performance for this match
            match_perf = {
                'runs': sum(p.get('runs', 0) for p in match.get('performances', [])),
                'wickets': sum(1 for p in match.get('performances', []) if p.get('wicket', False))
            }
            
            # Add to player
            player.add_match_condition(
                match_conditions.match_id,
                match_conditions.to_dict(),
                match_perf
            )
    
    def get_balance_score(self, player: Player) -> float:
        """Get how balanced a player is across conditions."""
        return player.get_conditions_balance_score()
    
    def identify_balanced_players(self, players: List[Player], threshold: float = 0.6) -> List[Player]:
        """Identify players who perform well across different conditions."""
        balanced = []
        for player in players:
            balance_score = self.get_balance_score(player)
            if balance_score >= threshold:
                balanced.append(player)
        return balanced

