"""Team bias modeler - Sam Curran effect and similar patterns."""

from typing import Dict, List, Tuple, Optional, Any
from models.player import Player
from models.team import Team
from dataclasses import dataclass


@dataclass
class BiasRelationship:
    """Bias relationship between player and team."""
    player_name: str
    target_team: str
    bias_score: float  # 0-1, higher = stronger bias
    reason: str
    performance_data: Dict[str, Any]
    match_context: str  # e.g., "playoff", "crucial", "regular"


class BiasModeler:
    """Model team bias patterns based on historical performance."""
    
    def __init__(self):
        """Initialize bias modeler."""
        self.bias_relationships: Dict[Tuple[str, str], BiasRelationship] = {}
    
    def calculate_bias_score(
        self,
        player: Player,
        target_team: str,
        performance_data: Dict[str, Any]
    ) -> Tuple[float, str]:
        """Calculate bias score for player against target team."""
        # Factors affecting bias:
        # 1. Exceptional performance (runs scored, wickets taken)
        # 2. Impact on team's key players
        # 3. Match context (playoffs, crucial games)
        
        runs_scored = performance_data.get('runs_against_team', 0)
        wickets_taken = performance_data.get('wickets_against_team', 0)
        key_player_dismissals = performance_data.get('key_player_dismissals', 0)
        match_context_score = performance_data.get('match_context_score', 0.5)  # 0-1
        
        # Normalize scores
        runs_score = min(runs_scored / 100.0, 1.0)  # 100+ runs = max score
        wickets_score = min(wickets_taken / 5.0, 1.0)  # 5+ wickets = max score
        key_dismissals_score = min(key_player_dismissals / 3.0, 1.0)  # 3+ key dismissals = max
        
        # Weighted combination
        bias_score = (
            runs_score * 0.3 +
            wickets_score * 0.4 +
            key_dismissals_score * 0.2 +
            match_context_score * 0.1
        )
        
        # Generate reason
        reasons = []
        if runs_score > 0.7:
            reasons.append(f"scored {runs_scored} runs")
        if wickets_score > 0.7:
            reasons.append(f"took {wickets_taken} wickets")
        if key_dismissals_score > 0.7:
            reasons.append(f"dismissed {key_player_dismissals} key players")
        if match_context_score > 0.7:
            reasons.append("in crucial matches")
        
        reason = f"Performed exceptionally against {target_team}: " + ", ".join(reasons) if reasons else "Moderate performance"
        
        return bias_score, reason
    
    def analyze_match_performance(
        self,
        player: Player,
        target_team: str,
        match_data: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze player's performance against target team in matches."""
        performance = {
            'runs_against_team': 0,
            'wickets_against_team': 0,
            'key_player_dismissals': 0,
            'match_context_score': 0.5,
            'matches': 0
        }
        
        # Get target team's key players (simplified - would need team data)
        # For now, assume any dismissal is important
        
        for match in match_data:
            match_info = match.get('match_data', {})
            teams = match_info.get('info', {}).get('teams', [])
            
            if target_team.upper() not in [t.upper() for t in teams]:
                continue
            
            performance['matches'] += 1
            
            # Check if crucial match
            event = match_info.get('meta', {}).get('event', '')
            if 'playoff' in event.lower() or 'final' in event.lower():
                performance['match_context_score'] = max(performance['match_context_score'], 0.9)
            elif 'qualifier' in event.lower():
                performance['match_context_score'] = max(performance['match_context_score'], 0.7)
            
            # Analyze performances
            for perf in match.get('performances', []):
                # Batting performance
                if perf.get('runs', 0) > 0:
                    performance['runs_against_team'] += perf['runs']
                
                # Bowling performance
                if perf.get('wicket', False):
                    performance['wickets_against_team'] += 1
                    # Assume key player dismissal (simplified)
                    performance['key_player_dismissals'] += 1
        
        return performance
    
    def add_bias_relationship(
        self,
        player: Player,
        target_team: str,
        match_data: List[Dict[str, Any]]
    ):
        """Add or update bias relationship."""
        performance_data = self.analyze_match_performance(player, target_team, match_data)
        
        if performance_data['matches'] == 0:
            return  # No matches against this team
        
        bias_score, reason = self.calculate_bias_score(player, target_team, performance_data)
        
        # Only add if bias score is significant
        if bias_score > 0.3:
            relationship = BiasRelationship(
                player_name=player.name,
                target_team=target_team,
                bias_score=bias_score,
                reason=reason,
                performance_data=performance_data,
                match_context="crucial" if performance_data['match_context_score'] > 0.7 else "regular"
            )
            
            self.bias_relationships[(player.name, target_team)] = relationship
    
    def get_bias_score(self, player_name: str, team_name: str) -> float:
        """Get bias score for player-team pair."""
        key = (player_name, team_name)
        if key in self.bias_relationships:
            return self.bias_relationships[key].bias_score
        return 0.0
    
    def get_bias_reason(self, player_name: str, team_name: str) -> Optional[str]:
        """Get bias reason for player-team pair."""
        key = (player_name, team_name)
        if key in self.bias_relationships:
            return self.bias_relationships[key].reason
        return None
    
    def get_all_biases_for_player(self, player_name: str) -> List[BiasRelationship]:
        """Get all bias relationships for a player."""
        return [
            rel for (p_name, _), rel in self.bias_relationships.items()
            if p_name == player_name
        ]
    
    def get_all_biases_for_team(self, team_name: str) -> List[BiasRelationship]:
        """Get all bias relationships for a team."""
        return [
            rel for (_, t_name), rel in self.bias_relationships.items()
            if t_name == team_name
        ]
    
    def to_dict(self) -> Dict:
        """Export bias relationships to dictionary."""
        return {
            'relationships': [
                {
                    'player_name': rel.player_name,
                    'target_team': rel.target_team,
                    'bias_score': rel.bias_score,
                    'reason': rel.reason,
                    'performance_data': rel.performance_data,
                    'match_context': rel.match_context
                }
                for rel in self.bias_relationships.values()
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'BiasModeler':
        """Import bias relationships from dictionary."""
        modeler = cls()
        for rel_data in data.get('relationships', []):
            relationship = BiasRelationship(
                player_name=rel_data['player_name'],
                target_team=rel_data['target_team'],
                bias_score=rel_data['bias_score'],
                reason=rel_data['reason'],
                performance_data=rel_data['performance_data'],
                match_context=rel_data['match_context']
            )
            modeler.bias_relationships[(rel_data['player_name'], rel_data['target_team'])] = relationship
        return modeler

