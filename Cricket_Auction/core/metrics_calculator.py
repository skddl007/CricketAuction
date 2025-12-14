"""Advanced metrics calculator (efscore, winp, raa) phase-wise."""

from typing import Dict, List, Optional, Any
from models.player import Player, PhaseMetrics
import statistics


class MetricsCalculator:
    """Calculate advanced metrics from ball-by-ball data."""
    
    def __init__(self):
        """Initialize calculator."""
        # Baseline averages (can be updated from historical data)
        self.baseline_pp_runs = 45  # Average runs in powerplay
        self.baseline_mo_runs = 60  # Average runs in middle overs
        self.baseline_death_runs = 50  # Average runs in death overs
    
    def calculate_efscore(self, expected_runs: float, actual_runs: float) -> float:
        """Calculate efscore (expected runs vs actual runs)."""
        if expected_runs == 0:
            return 0.0
        return (actual_runs / expected_runs) * 100
    
    def calculate_winp(self, match_context: Dict[str, Any], player_contribution: Dict[str, Any]) -> float:
        """Calculate win probability added (simplified version)."""
        # Simplified win probability calculation
        # In reality, this would use complex models
        base_winp = 0.5
        
        # Factors affecting win probability
        runs_factor = player_contribution.get('runs', 0) / 100.0
        wickets_factor = player_contribution.get('wickets', 0) * 0.1
        phase_factor = {
            'powerplay': 0.3,
            'middle_overs': 0.4,
            'death': 0.5
        }.get(player_contribution.get('phase', 'middle_overs'), 0.4)
        
        winp = base_winp + (runs_factor * phase_factor) + (wickets_factor * phase_factor)
        return min(max(winp, 0.0), 1.0)
    
    def calculate_raa(self, player_runs: float, phase: str, baseline: Optional[float] = None) -> float:
        """Calculate runs above average."""
        if baseline is None:
            baseline = {
                'powerplay': self.baseline_pp_runs,
                'middle_overs': self.baseline_mo_runs,
                'death': self.baseline_death_runs
            }.get(phase, 50)
        
        return player_runs - baseline
    
    def calculate_phase_metrics(self, performances: List[Dict[str, Any]], phase: str) -> Dict[str, float]:
        """Calculate metrics for a specific phase."""
        phase_performances = [p for p in performances if p.get('phase') == phase]
        
        if not phase_performances:
            return {'efscore': 0.0, 'winp': 0.0, 'raa': 0.0}
        
        # Calculate runs
        total_runs = sum(p.get('runs', 0) for p in phase_performances)
        total_overs = len(set(p.get('over', 0) for p in phase_performances))
        
        if total_overs == 0:
            return {'efscore': 0.0, 'winp': 0.0, 'raa': 0.0}
        
        runs_per_over = total_runs / total_overs
        
        # Expected runs (simplified - based on average)
        expected_runs = {
            'powerplay': self.baseline_pp_runs,
            'middle_overs': self.baseline_mo_runs,
            'death': self.baseline_death_runs
        }.get(phase, 50)
        
        # Calculate metrics
        efscore = self.calculate_efscore(expected_runs, total_runs)
        raa = self.calculate_raa(total_runs, phase, expected_runs)
        
        # Win probability (simplified)
        winp = self.calculate_winp(
            {'phase': phase, 'overs': total_overs},
            {'runs': total_runs, 'phase': phase, 'wickets': sum(1 for p in phase_performances if p.get('wicket', False))}
        )
        
        return {
            'efscore': efscore,
            'winp': winp,
            'raa': raa,
            'runs': total_runs,
            'overs': total_overs
        }
    
    def calculate_player_metrics(self, player: Player, match_data: List[Dict[str, Any]]) -> PhaseMetrics:
        """Calculate phase-wise metrics for a player."""
        metrics = PhaseMetrics()
        
        # Extract all performances
        all_performances = []
        for match in match_data:
            all_performances.extend(match.get('performances', []))
        
        if not all_performances:
            return metrics
        
        # Calculate for each phase
        metrics.powerplay = self.calculate_phase_metrics(all_performances, 'powerplay')
        metrics.middle_overs = self.calculate_phase_metrics(all_performances, 'middle_overs')
        metrics.death = self.calculate_phase_metrics(all_performances, 'death')
        
        return metrics
    
    def update_player_metrics(self, player: Player, match_data: List[Dict[str, Any]]):
        """Update player's advanced metrics."""
        metrics = self.calculate_player_metrics(player, match_data)
        player.advanced_metrics = metrics
    
    def calculate_all_players_metrics(self, players: List[Player], match_data_dict: Dict[str, List[Dict[str, Any]]]):
        """Calculate metrics for all players."""
        for player in players:
            if player.name in match_data_dict:
                self.update_player_metrics(player, match_data_dict[player.name])

