"""Supply & demand matrix generator."""

from typing import Dict, List, Any
from models.team import Team
from models.player import Player
from core.state_manager import StateManager
from core.playing11_analyzer import Playing11Analyzer


class MatrixGenerator:
    """Generate team-wise supply & demand matrices."""
    
    def __init__(self, state_manager: StateManager):
        """Initialize generator."""
        self.state_manager = state_manager
        self.playing11_analyzer = Playing11Analyzer()
    
    def generate_team_matrix(self, team: Team) -> str:
        """Generate matrix for a single team."""
        lines = []
        
        # Header
        lines.append(f"=== {team.name} ===")
        lines.append(f"Home Ground: {team.home_ground} ({team.ground_condition})")
        lines.append("")
        
        # Summary
        lines.append("Summary:")
        lines.append(f"  Total Players: {team.total_players}/{team.total_slots}")
        lines.append(f"  Foreign Players: {team.total_foreign_players}/{team.foreign_slots}")
        lines.append(f"  Purse Available: {team.purse_available / 100:.1f} Cr")
        lines.append(f"  Available Slots: {team.available_slots}")
        lines.append(f"  Available Foreign Slots: {team.available_foreign_slots}")
        lines.append("")
        
        # Players
        lines.append("Players:")
        lines.append("  Retained:")
        for player in team.retained_players:
            quality = f" ({player.quality.value})" if player.quality else ""
            lines.append(f"    - {player.name}{quality}")
        
        if team.bought_players:
            lines.append("  Bought:")
            for player in team.bought_players:
                quality = f" ({player.quality.value})" if player.quality else ""
                lines.append(f"    - {player.name}{quality}")
        
        lines.append("")
        
        # Speciality breakdown
        lines.append("Speciality Breakdown:")
        specialities = {}
        for player in team.get_all_players():
            if player.speciality:
                spec = player.speciality.value
                if spec not in specialities:
                    specialities[spec] = []
                specialities[spec].append(player.name)
        
        for spec, players in specialities.items():
            lines.append(f"  {spec}: {', '.join(players)}")
        
        lines.append("")
        
        # Quality breakdown
        lines.append("Quality Breakdown:")
        tier_a = [p.name for p in team.get_all_players() if p.quality and p.quality.value == 'A']
        tier_b = [p.name for p in team.get_all_players() if p.quality and p.quality.value == 'B']
        lines.append(f"  Tier A: {', '.join(tier_a) if tier_a else 'None'}")
        lines.append(f"  Tier B: {', '.join(tier_b) if tier_b else 'None'}")
        lines.append("")
        
        # Playing 11
        playing11 = self.playing11_analyzer.build_best_playing11(team)
        lines.append("Best Playing 11:")
        for i, player in enumerate(playing11, 1):
            lines.append(f"  {i}. {player.name}")
        lines.append("")
        
        # Gaps - using correct structure from identify_gaps
        gaps = self.playing11_analyzer.identify_gaps(team)
        lines.append("Identified Gaps:")
        
        role_gaps = gaps.get('role_gaps', {})
        quality_gaps = gaps.get('quality_gaps', {})
        
        if role_gaps.get('opener', 0) > 0:
            lines.append(f"  - Missing {role_gaps['opener']} opener(s)")
        if role_gaps.get('wk', 0) > 0:
            lines.append(f"  - Missing wicket-keeper")
        if role_gaps.get('spinner', 0) > 0:
            lines.append(f"  - Missing {role_gaps['spinner']} spinner(s)")
        if role_gaps.get('pacer', 0) > 0:
            lines.append(f"  - Missing {role_gaps['pacer']} pacer(s)")
        if role_gaps.get('finisher', 0) > 0:
            lines.append(f"  - Missing {role_gaps['finisher']} finisher(s)")
        if quality_gaps.get('tier_a_needed', 0) > 0:
            lines.append(f"  - Missing {quality_gaps['tier_a_needed']} Tier A player(s)")
        
        if gaps.get('total_gaps', 0) == 0:
            lines.append("  - No critical gaps identified")
        
        return "\n".join(lines)
    
    def generate_all_matrices(self) -> str:
        """Generate matrices for all teams."""
        teams = self.state_manager.get_all_teams()
        supply_count = self.state_manager.get_supply_count()
        
        lines = []
        for team_name, team in teams.items():
            lines.append(self.generate_team_matrix(team))
            lines.append("")
            lines.append("---")
            lines.append("")
        
        # Footer
        lines.append(f"State verified: {supply_count} players left in supply")
        
        return "\n".join(lines)

