"""Team requirement generator - LLM-driven from gap analysis (no hardcoded priorities)."""

from typing import Dict, List, Any
from models.team import Team
from core.playing11_analyzer import Playing11Analyzer


class TeamRequirementsGenerator:
    """Generate prioritized team requirements from gap analysis."""
    
    def __init__(self):
        """Initialize generator."""
        self.playing11_analyzer = Playing11Analyzer()
    
    def generate_requirements(self, team: Team) -> Dict[str, Any]:
        """
        Generate prioritized requirement list PURELY from gap analysis.
        
        Priority determined by:
        1. CRITICAL: Missing essential role → status='NotCheck' in batting_order or bowling_phases
        2. HIGH: Important gap → gap count > 0 in key specialities
        3. MEDIUM: Quality gap → Tier A count below target
        4. LOW: Depth/backup → secondary gaps
        
        NOTE: Priorities are NOT hardcoded; they derive from actual gaps.
        """
        # Get gaps analysis
        gaps_analysis = self.playing11_analyzer.analyze_team(team)
        batting_order = gaps_analysis['batting_order']
        bowling_phases = gaps_analysis['bowling_phases']
        gaps = gaps_analysis['gaps']
        
        requirements = []
        
        # CRITICAL: Find OPEN positions (NotCheck status)
        open_batting_positions = [bo for bo in batting_order if bo['status'] == 'NotCheck']
        if open_batting_positions:
            for pos in open_batting_positions:
                requirements.append({
                    'priority': 1,  # CRITICAL
                    'type': 'batting_order',
                    'position': pos['position'],
                    'required_tag': pos['speciality'],
                    'urgency': 'CRITICAL',
                    'reason': f"Batting position {pos['position']} OPEN - needs {pos['speciality']}"
                })
        
        # CRITICAL: Find RED phases (NotCheck status)
        open_phases = [bp for bp in bowling_phases if bp['status'] == 'NotCheck']
        if open_phases:
            for phase in open_phases:
                requirements.append({
                    'priority': 1,  # CRITICAL (RED phase per AuctionPrompt)
                    'type': 'bowling_phase',
                    'phase': phase['phase'],
                    'required_tag': f"#{phase['phase']}Bowler",
                    'urgency': 'CRITICAL',
                    'demand_boost': '+3 (RED phase)',
                    'reason': f"{phase['phase']} phase has NO primary bowler"
                })
        
        # HIGH: Check role-specific gaps
        role_gaps = gaps['role_gaps']
        
        if role_gaps.get('wk', 0) > 0:
            requirements.append({
                'priority': 1,  # CRITICAL - team must have WK
                'type': 'speciality',
                'speciality': 'WK',
                'gap_count': role_gaps['wk'],
                'urgency': 'CRITICAL',
                'reason': f"Team has no WK - auction rule violation risk"
            })
        
        if role_gaps.get('opener', 0) > 0:
            requirements.append({
                'priority': 2,  # HIGH
                'type': 'batting_role',
                'role': '#Opener',
                'gap_count': role_gaps['opener'],
                'urgency': 'HIGH',
                'reason': f"Need {role_gaps['opener']} opener(s) for playing 11"
            })
        
        if role_gaps.get('pacer', 0) > 0:
            requirements.append({
                'priority': 2,  # HIGH
                'type': 'bowling_role',
                'role': 'FastBowler',
                'gap_count': role_gaps['pacer'],
                'urgency': 'HIGH',
                'reason': f"Need {role_gaps['pacer']} pacer(s) for balanced bowling"
            })
        
        if role_gaps.get('spinner', 0) > 0:
            requirements.append({
                'priority': 2,  # HIGH
                'type': 'bowling_role',
                'role': 'SpinBowler',
                'gap_count': role_gaps['spinner'],
                'urgency': 'HIGH',
                'reason': f"Need {role_gaps['spinner']} spinner(s)"
            })
        
        if role_gaps.get('finisher', 0) > 0:
            requirements.append({
                'priority': 3,  # MEDIUM
                'type': 'batting_role',
                'role': '#Finisher',
                'gap_count': role_gaps['finisher'],
                'urgency': 'MEDIUM',
                'reason': f"Need {role_gaps['finisher']} finisher(s)"
            })
        
        # MEDIUM: Quality gaps
        quality_gaps = gaps['quality_gaps']
        if quality_gaps.get('tier_a_needed', 0) > 0:
            requirements.append({
                'priority': 3,  # MEDIUM
                'type': 'quality',
                'quality': 'Tier A',
                'gap_count': quality_gaps['tier_a_needed'],
                'urgency': 'MEDIUM',
                'reason': f"Target ~50% Tier A in squad; need {quality_gaps['tier_a_needed']} more"
            })
        
        # LOW: Depth/backup
        # Only add if all CRITICAL/HIGH gaps filled
        if all(gap['urgency'] not in ['CRITICAL', 'HIGH'] for gap in requirements):
            requirements.append({
                'priority': 4,  # LOW
                'type': 'depth',
                'role': 'Any',
                'urgency': 'LOW',
                'reason': 'Add depth/backup options'
            })
        
        # Sort by priority
        requirements.sort(key=lambda x: x['priority'])
        
        return {
            'team': team.name,
            'requirements': requirements,
            'total_requirements': len(requirements),
            'critical_requirements': len([r for r in requirements if r['urgency'] == 'CRITICAL']),
            'high_requirements': len([r for r in requirements if r['urgency'] == 'HIGH']),
            'gaps': gaps,
            'batting_order': batting_order,
            'bowling_phases': bowling_phases,
            'purse_available': team.purse_available,
            'available_slots': team.available_slots,
            'available_foreign_slots': team.available_foreign_slots
        }

