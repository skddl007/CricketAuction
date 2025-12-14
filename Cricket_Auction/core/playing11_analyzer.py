"""Playing 11 gap analyzer."""

from typing import Dict, List, Any, Optional
from models.team import Team
from models.player import Player


class Playing11Analyzer:
    """Analyze playing 11 and identify gaps."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def build_best_playing11(self, team: Team) -> List[Player]:
        """Build best possible playing 11 from retained players."""
        all_players = team.get_all_players()
        
        # Sort by quality (A > B) and role importance
        sorted_players = sorted(
            all_players,
            key=lambda p: (
                0 if p.quality and p.quality.value == 'A' else 1,
                self._get_role_priority(p)
            )
        )
        
        # Select best 11
        playing11 = []
        positions_filled = {
            'opener': 0,
            'middle_order': 0,
            'finisher': 0,
            'wk': 0,
            'pacer': 0,
            'spinner': 0,
            'all_rounder': 0
        }
        
        for player in sorted_players:
            if len(playing11) >= 11:
                break
            
            # Check if player fills a needed position
            if self._player_fills_gap(player, positions_filled):
                playing11.append(player)
                self._update_positions_filled(player, positions_filled)
        
        return playing11
    
    def _get_role_priority(self, player: Player) -> int:
        """Get priority for role (lower = higher priority)."""
        if player.primary_role:
            role_priority = {
                'Batter': 1,
                'Bowler': 2,
                'BatAR': 3,
                'BowlAR': 4,
                'Spinner': 5,
                'Pacer': 6
            }
            return role_priority.get(player.primary_role.value, 10)
        return 10
    
    def _player_fills_gap(self, player: Player, positions_filled: Dict[str, int]) -> bool:
        """Check if player fills a needed gap."""
        # Always add if we have less than 11
        if sum(positions_filled.values()) < 11:
            return True
        
        # Check specific gaps
        if player.batting_role and player.batting_role.value == 'Opener' and positions_filled['opener'] < 2:
            return True
        if player.speciality and player.speciality.value == 'WKBat' and positions_filled['wk'] < 1:
            return True
        if player.primary_role and 'Pacer' in player.primary_role.value and positions_filled['pacer'] < 3:
            return True
        if player.primary_role and 'Spinner' in player.primary_role.value and positions_filled['spinner'] < 2:
            return True
        
        return False
    
    def _update_positions_filled(self, player: Player, positions_filled: Dict[str, int]):
        """Update positions filled."""
        if player.batting_role:
            if player.batting_role.value == 'Opener':
                positions_filled['opener'] += 1
            elif player.batting_role.value in ['MiddleOrder', 'Finisher']:
                positions_filled['middle_order'] += 1
        
        if player.speciality and player.speciality.value == 'WKBat':
            positions_filled['wk'] += 1
        
        if player.primary_role:
            if 'Pacer' in player.primary_role.value:
                positions_filled['pacer'] += 1
            if 'Spinner' in player.primary_role.value:
                positions_filled['spinner'] += 1
            if 'AR' in player.primary_role.value:
                positions_filled['all_rounder'] += 1
    
    def identify_gaps(self, team: Team) -> Dict[str, Any]:
        """Identify gaps in playing 11."""
        playing11 = self.build_best_playing11(team)
        all_players = team.get_all_players()
        
        gaps = {
            'batting_positions': {
                'opener': 2,
                'middle_order': 4,
                'finisher': 1
            },
            'bowling_phases': {
                'powerplay': 0,
                'middle_overs': 0,
                'death': 0
            },
            'speciality_roles': {
                'wk': 1,
                'spinner': 2,
                'pacer': 3,
                'all_rounder': 1
            },
            'quality_gaps': {
                'tier_a_needed': 0,
                'tier_b_acceptable': 0
            }
        }
        
        # Count what we have
        for player in playing11:
            # Batting positions
            if player.batting_role:
                if player.batting_role.value == 'Opener':
                    gaps['batting_positions']['opener'] = max(0, gaps['batting_positions']['opener'] - 1)
                elif player.batting_role.value == 'MiddleOrder':
                    gaps['batting_positions']['middle_order'] = max(0, gaps['batting_positions']['middle_order'] - 1)
                elif player.batting_role.value == 'Finisher':
                    gaps['batting_positions']['finisher'] = max(0, gaps['batting_positions']['finisher'] - 1)
            
            # Speciality roles
            if player.speciality and player.speciality.value == 'WKBat':
                gaps['speciality_roles']['wk'] = max(0, gaps['speciality_roles']['wk'] - 1)
            
            # Bowling roles
            if player.bowling_role:
                if 'Pacer' in player.bowling_role.value or 'Fast' in player.bowling_role.value:
                    gaps['speciality_roles']['pacer'] = max(0, gaps['speciality_roles']['pacer'] - 1)
                if 'Spin' in player.bowling_role.value:
                    gaps['speciality_roles']['spinner'] = max(0, gaps['speciality_roles']['spinner'] - 1)
            
            if player.primary_role and 'AR' in player.primary_role.value:
                gaps['speciality_roles']['all_rounder'] = max(0, gaps['speciality_roles']['all_rounder'] - 1)
            
            # Quality
            if player.quality and player.quality.value == 'A':
                gaps['quality_gaps']['tier_a_needed'] = max(0, gaps['quality_gaps']['tier_a_needed'] - 1)
        
        # Bowling phases
        for player in playing11:
            if player.speciality:
                if player.speciality.value == 'PPBowler':
                    gaps['bowling_phases']['powerplay'] = max(0, gaps['bowling_phases']['powerplay'] - 1)
                elif player.speciality.value == 'MOBowler':
                    gaps['bowling_phases']['middle_overs'] = max(0, gaps['bowling_phases']['middle_overs'] - 1)
                elif player.speciality.value == 'DeathBowler':
                    gaps['bowling_phases']['death'] = max(0, gaps['bowling_phases']['death'] - 1)
        
        # Calculate total gaps
        total_gaps = (
            sum(gaps['batting_positions'].values()) +
            sum(gaps['bowling_phases'].values()) +
            sum(gaps['speciality_roles'].values())
        )
        
        gaps['total_gaps'] = total_gaps
        gaps['playing11_size'] = len(playing11)
        gaps['playing11'] = [p.name for p in playing11]
        
        return gaps
    
    def analyze_batting_order(self, team: Team) -> List[Dict[str, Any]]:
        """Analyze batting order positions (Step h from prompt)."""
        playing11 = self.build_best_playing11(team)
        batting_order = []
        
        # Expected positions: 1-11
        positions_needed = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        position_map = {}
        
        # Map players to positions based on their roles
        for pos in positions_needed:
            player_found = None
            player_tier = None
            speciality = None
            status = "NotCheck"
            
            # Position 1-2: Openers
            if pos <= 2:
                for player in playing11:
                    if player.batting_role and player.batting_role.value == 'Opener':
                        if pos not in position_map:
                            player_found = player.name
                            player_tier = player.quality.value if player.quality else 'B'
                            speciality = 'Opener'
                            status = "Check"
                            position_map[pos] = player
                            break
            
            # Position 3-5: Top/Middle order
            elif pos <= 5:
                for player in playing11:
                    if player.batting_role and player.batting_role.value in ['MiddleOrder', 'Top3Anchor']:
                        if player not in position_map.values():
                            player_found = player.name
                            player_tier = player.quality.value if player.quality else 'B'
                            speciality = player.primary_role.value if player.primary_role else 'Batter'
                            status = "Check"
                            position_map[pos] = player
                            break
            
            # Position 6-7: Finishers/All-rounders
            elif pos <= 7:
                for player in playing11:
                    if (player.batting_role and player.batting_role.value == 'Finisher') or \
                       (player.primary_role and 'AR' in player.primary_role.value):
                        if player not in position_map.values():
                            player_found = player.name
                            player_tier = player.quality.value if player.quality else 'B'
                            speciality = player.primary_role.value if player.primary_role else 'Finisher'
                            status = "Check"
                            position_map[pos] = player
                            break
            
            # Position 8-11: Bowlers
            else:
                for player in playing11:
                    if player.primary_role and player.primary_role.value in ['Bowler', 'Pacer', 'Spinner']:
                        if player not in position_map.values():
                            player_found = player.name
                            player_tier = player.quality.value if player.quality else 'B'
                            speciality = player.primary_role.value
                            status = "Check"
                            position_map[pos] = player
                            break
            
            if not player_found:
                player_found = "[OPEN]"
                speciality = self._get_required_speciality_for_position(pos)
                status = "NotCheck"
            
            batting_order.append({
                'team': team.name,
                'position': pos,
                'player': player_found,
                'tier': player_tier,
                'speciality': speciality,
                'status': status
            })
        
        return batting_order
    
    def _get_required_speciality_for_position(self, pos: int) -> str:
        """Get required speciality for a batting position."""
        if pos <= 2:
            return 'Opener'
        elif pos <= 5:
            return 'MiddleOrder'
        elif pos <= 7:
            return 'Finisher/BatAR'
        else:
            return 'Bowler'
    
    def analyze_bowling_phases(self, team: Team) -> List[Dict[str, Any]]:
        """Analyze bowling phase coverage (Step i from prompt)."""
        playing11 = self.build_best_playing11(team)
        phases = ['Powerplay', 'MiddleOvers', 'Death']
        bowling_analysis = []
        
        for phase in phases:
            primary_bowlers = []
            backup_bowlers = []
            status = "NotCheck"
            
            for player in playing11:
                if not player.bowling_role and not player.primary_role:
                    continue
                
                # Check if player can bowl in this phase
                can_bowl = False
                if phase == 'Powerplay':
                    can_bowl = (
                        player.speciality and 'PPBowler' in player.speciality.value or
                        (player.bowling_role and 'Pace' in player.bowling_role.value) or
                        (player.primary_role and 'Pacer' in player.primary_role.value)
                    )
                elif phase == 'MiddleOvers':
                    can_bowl = (
                        player.speciality and 'MOBowler' in player.speciality.value or
                        (player.bowling_role and 'Spin' in player.bowling_role.value) or
                        (player.primary_role and 'Spinner' in player.primary_role.value) or
                        (player.primary_role and 'AR' in player.primary_role.value)
                    )
                elif phase == 'Death':
                    can_bowl = (
                        player.speciality and 'DeathBowler' in player.speciality.value or
                        (player.bowling_role and ('Pace' in player.bowling_role.value or 'Fast' in player.bowling_role.value)) or
                        (player.primary_role and 'Pacer' in player.primary_role.value)
                    )
                
                if can_bowl:
                    if player.quality and player.quality.value == 'A':
                        primary_bowlers.append(player.name)
                    else:
                        backup_bowlers.append(player.name)
            
            # Determine status
            if len(primary_bowlers) >= 2:
                status = "Check"
            elif len(primary_bowlers) >= 1 or len(backup_bowlers) >= 2:
                status = "Adjusted"
            else:
                status = "NotCheck"
            
            primary_str = "/".join(primary_bowlers[:3]) if primary_bowlers else "[OPEN]"
            backup_str = "/".join(backup_bowlers[:2]) if backup_bowlers else "None"
            
            bowling_analysis.append({
                'team': team.name,
                'phase': phase,
                'primary': primary_str,
                'backup': backup_str,
                'status': status
            })
        
        return bowling_analysis
    
    def analyze_team(self, team: Team) -> Dict[str, Any]:
        """Complete team analysis with enhanced gap analysis."""
        playing11 = self.build_best_playing11(team)
        gaps = self.identify_gaps(team)
        batting_order = self.analyze_batting_order(team)
        bowling_phases = self.analyze_bowling_phases(team)
        
        # Identify weak points based on gaps
        weak_points = []
        
        # Check batting order gaps
        open_positions = [bo for bo in batting_order if bo['status'] == 'NotCheck']
        if open_positions:
            weak_points.append({
                'category': 'Batting Order',
                'severity': 'High',
                'details': f"Missing players for positions: {[bo['position'] for bo in open_positions]}",
                'required_speciality': [bo['speciality'] for bo in open_positions]
            })
        
        # Check bowling phase gaps
        critical_phases = [bp for bp in bowling_phases if bp['status'] == 'NotCheck']
        if critical_phases:
            weak_points.append({
                'category': 'Bowling Phases',
                'severity': 'High',
                'details': f"Missing coverage for phases: {[bp['phase'] for bp in critical_phases]}",
                'required_roles': [bp['phase'] + 'Bowler' for bp in critical_phases]
            })
        
        # Check speciality gaps
        if gaps['speciality_roles']['wk'] > 0:
            weak_points.append({
                'category': 'Wicket Keeper',
                'severity': 'Critical',
                'details': 'Missing wicket-keeper in playing 11',
                'required_roles': ['WKBat']
            })
        
        if gaps['speciality_roles']['pacer'] > 0:
            weak_points.append({
                'category': 'Pace Bowling',
                'severity': 'High',
                'details': f"Need {gaps['speciality_roles']['pacer']} more pace bowler(s)",
                'required_roles': ['Pacer', 'FastBowler']
            })
        
        if gaps['speciality_roles']['spinner'] > 0:
            weak_points.append({
                'category': 'Spin Bowling',
                'severity': 'Medium',
                'details': f"Need {gaps['speciality_roles']['spinner']} more spinner(s)",
                'required_roles': ['Spinner']
            })
        
        # Check purse constraints
        if team.purse_available < 1000:  # Less than 10 Cr
            weak_points.append({
                'category': 'Purse Constraint',
                'severity': 'Medium',
                'details': f"Limited purse remaining: {team.purse_available/100:.2f} Cr",
                'required_roles': ['Budget options needed']
            })
        
        return {
            'team': team.name,
            'playing11': [p.name for p in playing11],
            'gaps': gaps,
            'batting_order': batting_order,
            'bowling_phases': bowling_phases,
            'weak_points': weak_points,
            'total_players': team.total_players,
            'available_slots': team.available_slots,
            'purse_available': team.purse_available,
            'purse_available_cr': team.purse_available / 100.0
        }

