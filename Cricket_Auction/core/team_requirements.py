"""Team requirement generator combining gaps and home ground needs."""

from typing import Dict, List, Any
from models.team import Team
from core.playing11_analyzer import Playing11Analyzer
from core.home_ground_analyzer import HomeGroundAnalyzer


class TeamRequirementsGenerator:
    """Generate prioritized team requirements."""
    
    def __init__(self):
        """Initialize generator."""
        self.playing11_analyzer = Playing11Analyzer()
        self.home_ground_analyzer = HomeGroundAnalyzer()
    
    def generate_requirements(self, team: Team) -> Dict[str, Any]:
        """Generate prioritized requirement list for team."""
        # Get gaps
        gaps_analysis = self.playing11_analyzer.analyze_team(team)
        gaps = gaps_analysis['gaps']
        
        # Get home ground requirements
        ground_analysis = self.home_ground_analyzer.analyze_team_ground_fit(team)
        
        # Combine and prioritize
        requirements = []
        
        # Priority 1: Critical gaps (missing essential roles)
        if gaps['speciality_roles']['wk'] > 0:
            requirements.append({
                'priority': 1,
                'type': 'speciality',
                'role': 'WKBat',
                'urgency': 'critical',
                'reason': 'Missing wicket-keeper'
            })
        
        if gaps['batting_positions']['opener'] > 0:
            requirements.append({
                'priority': 1,
                'type': 'batting',
                'role': 'Opener',
                'urgency': 'critical',
                'reason': f"Missing {gaps['batting_positions']['opener']} opener(s)"
            })
        
        # Priority 2: Important gaps (bowling phases)
        if gaps['bowling_phases']['death'] > 0:
            requirements.append({
                'priority': 2,
                'type': 'bowling',
                'role': 'DeathBowler',
                'urgency': 'high',
                'reason': 'Missing death over bowler'
            })
        
        if gaps['bowling_phases']['powerplay'] > 0:
            requirements.append({
                'priority': 2,
                'type': 'bowling',
                'role': 'PPBowler',
                'urgency': 'high',
                'reason': 'Missing powerplay bowler'
            })
        
        # Priority 3: Home ground requirements
        for req in ground_analysis['requirements_missing']:
            if 'spinner' in req.lower():
                requirements.append({
                    'priority': 3,
                    'type': 'home_ground',
                    'role': 'Spinner',
                    'urgency': 'medium',
                    'reason': f"Home ground requirement: {req}"
                })
            elif 'pacer' in req.lower():
                requirements.append({
                    'priority': 3,
                    'type': 'home_ground',
                    'role': 'Pacer',
                    'urgency': 'medium',
                    'reason': f"Home ground requirement: {req}"
                })
        
        # Priority 4: Quality gaps
        if gaps['quality_gaps']['tier_a_needed'] > 0:
            requirements.append({
                'priority': 4,
                'type': 'quality',
                'role': 'TierA',
                'urgency': 'medium',
                'reason': 'Need Tier A players'
            })
        
        # Priority 5: Depth and backup
        if gaps['batting_positions']['middle_order'] > 0:
            requirements.append({
                'priority': 5,
                'type': 'batting',
                'role': 'MiddleOrder',
                'urgency': 'low',
                'reason': f"Need {gaps['batting_positions']['middle_order']} middle order player(s)"
            })
        
        # Sort by priority
        requirements.sort(key=lambda x: x['priority'])
        
        return {
            'team': team.name,
            'requirements': requirements,
            'total_requirements': len(requirements),
            'critical_requirements': len([r for r in requirements if r['urgency'] == 'critical']),
            'gaps': gaps,
            'ground_analysis': ground_analysis,
            'purse_available': team.purse_available,
            'available_slots': team.available_slots,
            'available_foreign_slots': team.available_foreign_slots
        }

