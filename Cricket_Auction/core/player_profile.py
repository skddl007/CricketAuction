"""Player profile generator with advanced metrics and conditions."""

from typing import Dict, Any, Optional
from models.player import Player


class PlayerProfileGenerator:
    """Generate comprehensive player profiles."""
    
    def generate_profile(self, player: Player) -> Dict[str, Any]:
        """Generate comprehensive player profile."""
        profile = {
            'name': player.name,
            'country': player.country,
            'base_price': player.base_price,
            'batting_hand': player.batting_hand,
            'bowling_style': player.bowling_style,
            'primary_role': player.primary_role.value if player.primary_role else None,
            'batting_role': player.batting_role.value if player.batting_role else None,
            'bowling_role': player.bowling_role.value if player.bowling_role else None,
            'speciality': player.speciality.value if player.speciality else None,
            'quality': player.quality.value if player.quality else None,
            'bat_utilization': player.bat_utilization,
            'bowl_utilization': player.bowl_utilization,
            'international_leagues': player.international_leagues,
            'ipl_experience': player.ipl_experience,
            'scouting': player.scouting,
            'smat_performance': player.smat_performance
        }
        
        # Add advanced metrics
        if player.advanced_metrics:
            profile['advanced_metrics'] = {
                'powerplay': {
                    'efscore': player.advanced_metrics.powerplay.get('efscore') if player.advanced_metrics.powerplay else None,
                    'winp': player.advanced_metrics.powerplay.get('winp') if player.advanced_metrics.powerplay else None,
                    'raa': player.advanced_metrics.powerplay.get('raa') if player.advanced_metrics.powerplay else None
                },
                'middle_overs': {
                    'efscore': player.advanced_metrics.middle_overs.get('efscore') if player.advanced_metrics.middle_overs else None,
                    'winp': player.advanced_metrics.middle_overs.get('winp') if player.advanced_metrics.middle_overs else None,
                    'raa': player.advanced_metrics.middle_overs.get('raa') if player.advanced_metrics.middle_overs else None
                },
                'death': {
                    'efscore': player.advanced_metrics.death.get('efscore') if player.advanced_metrics.death else None,
                    'winp': player.advanced_metrics.death.get('winp') if player.advanced_metrics.death else None,
                    'raa': player.advanced_metrics.death.get('raa') if player.advanced_metrics.death else None
                }
            }
        else:
            profile['advanced_metrics'] = None
        
        # Add conditions performance
        profile['conditions_performance'] = player.performance_by_conditions
        profile['conditions_balance_score'] = player.get_conditions_balance_score()
        profile['conditions_adaptability'] = player.metadata.get('conditions_adaptability', 0.5)
        
        # Add match conditions
        profile['match_conditions_count'] = len(player.match_conditions)
        
        return profile
    
    def format_profile_for_display(self, player: Player) -> str:
        """Format player profile for display."""
        profile = self.generate_profile(player)
        
        lines = [
            f"=== {profile['name']} ===",
            f"Country: {profile['country']} | Base Price: {profile['base_price']}L",
            f"Role: {profile['primary_role']} | Quality: {profile['quality']}",
        ]
        
        if profile['batting_role']:
            lines.append(f"Batting: {profile['batting_role']} ({profile['batting_hand']})")
        
        if profile['bowling_role']:
            lines.append(f"Bowling: {profile['bowling_role']}")
        
        if profile['speciality']:
            lines.append(f"Speciality: {profile['speciality']}")
        
        if profile['bat_utilization']:
            lines.append(f"Bat Utilization: {', '.join(profile['bat_utilization'])}")
        
        if profile['bowl_utilization']:
            lines.append(f"Bowl Utilization: {', '.join(profile['bowl_utilization'])}")
        
        # Advanced metrics
        if profile['advanced_metrics']:
            lines.append("\nAdvanced Metrics:")
            for phase in ['powerplay', 'middle_overs', 'death']:
                phase_data = profile['advanced_metrics'][phase]
                if phase_data and any(v is not None for v in phase_data.values()):
                    lines.append(f"  {phase.replace('_', ' ').title()}: "
                              f"efscore={phase_data.get('efscore', 'N/A')}, "
                              f"winp={phase_data.get('winp', 'N/A')}, "
                              f"raa={phase_data.get('raa', 'N/A')}")
        
        # Conditions
        lines.append(f"\nConditions Balance Score: {profile['conditions_balance_score']:.2f}")
        lines.append(f"Conditions Adaptability: {profile['conditions_adaptability']:.2f}")
        
        return "\n".join(lines)

