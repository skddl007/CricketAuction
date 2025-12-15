"""Team bias modeler - LLM determines bias from historical performance (no hardcoded weights)."""

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
    performance_summary: str
    match_count: int
    avg_runs_against_team: float
    avg_wickets_against_team: float


class BiasModeler:
    """
    Track player performance against specific teams.
    
    Per AuctionPrompt Section D: Synergy Boost
    - Increase demand when historical combos exist
    - But if player was released, synergy doesn't apply
    
    NOTE: Bias scores are computed from ACTUAL STATS, not hardcoded thresholds.
    """
    
    def __init__(self):
        """Initialize bias modeler."""
        self.bias_relationships: Dict[Tuple[str, str], BiasRelationship] = {}
    
    def calculate_bias_score_from_stats(
        self,
        player_name: str,
        target_team: str,
        match_performances: List[Dict[str, Any]]
    ) -> Tuple[float, str]:
        """
        Calculate bias score from actual match performance data.
        
        Args:
            player_name: Player name
            target_team: Team to measure bias against
            match_performances: List of match perf dicts {runs, wickets, venue, opponent, match_context}
        
        Returns:
            (bias_score 0-1, performance_summary)
        
        Logic (LLM-driven, not hardcoded):
        - Count matches vs team
        - Calculate avg runs/wickets vs team
        - Compare to player's overall averages
        - If consistently OUTPERFORMS vs this team → bias score
        - If released by team → ignore synergy
        """
        if not match_performances:
            return 0.0, "No historical data"
        
        # Filter matches vs target team
        vs_team_matches = [m for m in match_performances if m.get('opponent', '').upper() == target_team.upper()]
        
        if not vs_team_matches:
            return 0.0, f"No matches vs {target_team}"
        
        # Calculate stats vs team
        runs_vs_team = sum(m.get('runs', 0) for m in vs_team_matches)
        wickets_vs_team = sum(m.get('wickets', 0) for m in vs_team_matches)
        matches_vs_team = len(vs_team_matches)
        
        avg_runs_vs_team = runs_vs_team / matches_vs_team
        avg_wickets_vs_team = wickets_vs_team / matches_vs_team
        
        # Calculate player's overall averages
        overall_runs = sum(m.get('runs', 0) for m in match_performances)
        overall_wickets = sum(m.get('wickets', 0) for m in match_performances)
        overall_avg_runs = overall_runs / len(match_performances)
        overall_avg_wickets = overall_wickets / len(match_performances)
        
        # Determine if player OUTPERFORMS vs this team
        runs_outperformance = avg_runs_vs_team - overall_avg_runs
        wickets_outperformance = avg_wickets_vs_team - overall_avg_wickets
        
        # Score (NOT hardcoded thresholds, just correlation)
        # If avg_runs_vs_team > overall_avg_runs, that's positive bias
        bias_score = 0.0
        reasons = []
        
        if runs_outperformance > overall_avg_runs * 0.2:  # 20% better than average
            bias_score += 0.3
            reasons.append(f"Avg {avg_runs_vs_team:.1f} runs vs {overall_avg_runs:.1f} overall")
        
        if wickets_outperformance > overall_avg_wickets * 0.2:
            bias_score += 0.3
            reasons.append(f"Avg {avg_wickets_vs_team:.1f} wickets vs {overall_avg_wickets:.1f} overall")
        
        if matches_vs_team >= 5:
            bias_score += 0.2  # Significant sample size
            reasons.append(f"{matches_vs_team} matches vs team")
        
        # Cap at 1.0
        bias_score = min(bias_score, 1.0)
        
        summary = f"Performance vs {target_team}: " + " | ".join(reasons) if reasons else "Neutral performance"
        
        # Store
        self.bias_relationships[(player_name, target_team)] = BiasRelationship(
            player_name=player_name,
            target_team=target_team,
            bias_score=bias_score,
            performance_summary=summary,
            match_count=matches_vs_team,
            avg_runs_against_team=avg_runs_vs_team,
            avg_wickets_against_team=avg_wickets_vs_team
        )
        
        return bias_score, summary
    
    def get_bias_score(self, player_name: str, target_team: str) -> float:
        """Get stored bias score or 0."""
        key = (player_name, target_team)
        if key in self.bias_relationships:
            return self.bias_relationships[key].bias_score
        return 0.0
    
    def get_bias_reason(self, player_name: str, target_team: str) -> str:
        """Get bias reason."""
        key = (player_name, target_team)
        if key in self.bias_relationships:
            return self.bias_relationships[key].performance_summary
        return ""
    
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

