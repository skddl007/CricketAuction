"""Home ground conditions analyzer."""

from typing import Dict, List, Any
from models.team import Team


class HomeGroundAnalyzer:
    """Analyze home ground conditions and requirements."""
    
    # Home ground conditions mapping
    GROUND_CONDITIONS = {
        'CSK': {
            'ground': 'Chepauk',
            'condition': 'spin-friendly',
            'requirements': ['needs spinners', 'needs spin all-rounders'],
            'favors': ['spinners', 'spin hitters']
        },
        'RCB': {
            'ground': 'Chinnaswamy',
            'condition': 'batting-friendly',
            'requirements': ['needs power hitters', 'small boundaries'],
            'favors': ['power hitters', 'pace bowlers']
        },
        'MI': {
            'ground': 'Wankhede',
            'condition': 'pace-friendly',
            'requirements': ['needs pacers', 'needs pace all-rounders'],
            'favors': ['pacers', 'pace hitters']
        },
        'KKR': {
            'ground': 'Eden Gardens',
            'condition': 'balanced',
            'requirements': ['slightly favors pace'],
            'favors': ['balanced players']
        },
        'DC': {
            'ground': 'Arun Jaitley',
            'condition': 'balanced',
            'requirements': [],
            'favors': ['balanced players']
        },
        'GT': {
            'ground': 'Ahmedabad',
            'condition': 'pace-friendly',
            'requirements': ['needs pacers'],
            'favors': ['pacers']
        },
        'LSG': {
            'ground': 'Lucknow',
            'condition': 'balanced',
            'requirements': [],
            'favors': ['balanced players']
        },
        'PBKS': {
            'ground': 'Mohali',
            'condition': 'pace-friendly',
            'requirements': ['needs pacers'],
            'favors': ['pacers']
        },
        'RR': {
            'ground': 'Jaipur',
            'condition': 'balanced',
            'requirements': ['slightly favors spin'],
            'favors': ['spinners', 'balanced players']
        },
        'SRH': {
            'ground': 'Hyderabad',
            'condition': 'balanced',
            'requirements': ['slightly favors pace'],
            'favors': ['pacers', 'balanced players']
        }
    }
    
    def get_ground_requirements(self, team: Team) -> List[str]:
        """Get home ground requirements for team."""
        team_key = team.name.upper()
        if team_key in self.GROUND_CONDITIONS:
            return self.GROUND_CONDITIONS[team_key]['requirements']
        return []
    
    def get_ground_favors(self, team: Team) -> List[str]:
        """Get what the ground favors."""
        team_key = team.name.upper()
        if team_key in self.GROUND_CONDITIONS:
            return self.GROUND_CONDITIONS[team_key]['favors']
        return []
    
    def analyze_team_ground_fit(self, team: Team) -> Dict[str, Any]:
        """Analyze how well team fits home ground."""
        team_key = team.name.upper()
        if team_key not in self.GROUND_CONDITIONS:
            return {'fit_score': 0.5, 'requirements_met': [], 'requirements_missing': []}
        
        ground_info = self.GROUND_CONDITIONS[team_key]
        requirements = ground_info['requirements']
        favors = ground_info['favors']
        
        # Check which requirements are met
        requirements_met = []
        requirements_missing = []
        
        all_players = team.get_all_players()
        
        for req in requirements:
            met = False
            if 'spinner' in req.lower():
                met = any(
                    p.primary_role and 'Spin' in p.primary_role.value or
                    p.bowling_role and 'Spin' in p.bowling_role.value
                    for p in all_players
                )
            elif 'pacer' in req.lower():
                met = any(
                    p.primary_role and 'Pacer' in p.primary_role.value or
                    p.bowling_role and 'Pacer' in p.bowling_role.value
                    for p in all_players
                )
            elif 'power hitter' in req.lower():
                met = any('PowerHitter' in p.bat_utilization for p in all_players)
            
            if met:
                requirements_met.append(req)
            else:
                requirements_missing.append(req)
        
        # Calculate fit score
        if requirements:
            fit_score = len(requirements_met) / len(requirements)
        else:
            fit_score = 0.5  # Balanced ground
        
        return {
            'ground': ground_info['ground'],
            'condition': ground_info['condition'],
            'requirements': requirements,
            'favors': favors,
            'requirements_met': requirements_met,
            'requirements_missing': requirements_missing,
            'fit_score': fit_score
        }

