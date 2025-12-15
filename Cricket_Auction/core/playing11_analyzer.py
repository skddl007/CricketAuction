"""Playing 11 gap analyzer - LLM-driven (no hardcoded rules)."""

from typing import Dict, List, Any, Optional
from models.team import Team
from models.player import Player


class Playing11Analyzer:
    """Analyze playing 11 and identify gaps based on player TAGS, not hardcoded rules."""
    
    def __init__(self):
        """Initialize analyzer."""
        pass
    
    def build_best_playing11(self, team: Team) -> List[Player]:
        """
        Build best possible playing 11 from ONLY retained players.
        
        Strategy (from AuctionPrompt Step h/i):
        - Sort by Quality Tier (A > B) 
        - Select players with explicit batting/bowling tags
        - Ensure coverage of key specialities: WK, Opener, Finisher, Pacer, Spinner
        - Fill remaining slots by primary role quality
        
        NOTE: Exact positional mapping (1-11) is done by LLM in analyze_batting_order()
        based on player TAGS, not by this method.
        """
        retained_only = team.retained_players
        
        if not retained_only:
            return []
        
        # Sort by quality (A > B) - primary selection criterion per AuctionPrompt Step c
        sorted_players = sorted(
            retained_only,
            key=lambda p: (
                0 if p.quality and p.quality.value == 'A' else 1,
                self._get_role_priority(p)
            )
        )
        
        # Track coverage of mandatory roles from tags
        role_coverage = {
            'wk': False,        # Needs #WK tag
            'opener': False,    # Needs #Opener tag
            'finisher': False,  # Needs #Finisher tag
            'pacer': False,     # Needs #RightArmFast or #LeftArmPace tag
            'spinner': False    # Needs #Legspin, #Offspin, #MysterySpinner tag
        }
        
        selected = []
        mandatory_players = []
        optional_players = []
        
        # First pass: identify mandatory role players via their tags
        for player in sorted_players:
            if not mandatory_players and player.speciality:
                if player.speciality.value == 'WK' or self._has_wk_tag(player):
                    mandatory_players.append(player)
                    role_coverage['wk'] = True
        
        # Add other players sorted by quality and role fit
        for player in sorted_players:
            if player not in mandatory_players:
                optional_players.append(player)
        
        # Select top 11 by quality, ensuring mandatory roles covered
        selected = mandatory_players
        for player in optional_players:
            if len(selected) >= 11:
                break
            selected.append(player)
        
        return selected[:11]
    
    def _has_wk_tag(self, player: Player) -> bool:
        """Check if player has WK-related tag."""
        # Check batting_tags or speciality for WK indicator
        if hasattr(player, 'tags') and player.tags:
            return '#WK' in str(player.tags)
        return False
    
    def _get_role_priority(self, player: Player) -> int:
        """
        Get priority for role based on speciality (lower = higher priority).
        Per AuctionPrompt Step b: speciality is one of [Batter, BatAR, BowlAR, SpinBowler, FastBowler].
        """
        if player.speciality:
            role_priority = {
                'Batter': 1,           # Always prefer pure batters for batting depth
                'BatAR': 2,            # Bat-dominant AR
                'BowlAR': 3,           # Bowl-dominant AR
                'SpinBowler': 4,       # Pure spin
                'FastBowler': 5        # Pure pace
            }
            return role_priority.get(player.speciality.value, 10)
        return 10
    
    def identify_gaps(self, team: Team) -> Dict[str, Any]:
        """
        Identify gaps in playing 11 based on retained players ONLY.
        
        Per AuctionPrompt:
        - Step h: Batting order gaps based on player TAGS (#Opener, #MiddleOrder, #Finisher)
        - Step i: Bowling phase gaps based on SPECIALITIES (#PPBowler, #MiddleOvers, #DeathBowler)
        - Quality gaps based on Tier A/B distribution
        
        NOTE: This method provides gap ANALYSIS only.
        LLM in recommender.py will fill these gaps from auction supply.
        """
        playing11 = self.build_best_playing11(team)
        
        # Count key roles in playing11
        wk_count = sum(1 for p in playing11 if p.speciality and (p.speciality.value == 'WK' or self._has_wk_tag(p)))
        opener_count = sum(1 for p in playing11 if hasattr(p, 'batting_tags') and '#Opener' in str(p.batting_tags))
        finisher_count = sum(1 for p in playing11 if hasattr(p, 'batting_tags') and '#Finisher' in str(p.batting_tags))
        pacer_count = sum(1 for p in playing11 if p.speciality and p.speciality.value == 'FastBowler')
        spinner_count = sum(1 for p in playing11 if p.speciality and p.speciality.value == 'SpinBowler')
        
        # Count Tier A players
        tier_a_count = sum(1 for p in playing11 if p.quality and p.quality.value == 'A')
        
        gaps = {
            'role_gaps': {
                'wk': max(0, 1 - wk_count),                    # Need at least 1 WK per AuctionPrompt
                'opener': max(0, 2 - opener_count),            # Need at least 2 openers
                'finisher': max(0, 1 - finisher_count),        # Need at least 1 finisher
                'pacer': max(0, 3 - pacer_count),              # 3+ pacers for balance
                'spinner': max(0, 2 - spinner_count)           # 2+ spinners for balance
            },
            'bowling_phase_gaps': {
                # LLM will determine if PP/Middle/Death coverage is adequate via analyze_bowling_phases()
                'powerplay_specialist': 0,
                'middle_overs_specialist': 0,
                'death_specialist': 0
            },
            'quality_gaps': {
                'tier_a_needed': max(0, 5 - tier_a_count)      # Target ~50% Tier A in playing 11
            },
            'playing11_composition': {
                'wk_count': wk_count,
                'opener_count': opener_count,
                'finisher_count': finisher_count,
                'pacer_count': pacer_count,
                'spinner_count': spinner_count,
                'tier_a_count': tier_a_count
            },
            'total_gaps': 0,
            'playing11_size': len(playing11),
            'playing11': [p.name for p in playing11]
        }
        
        # Calculate total role gaps
        gaps['total_gaps'] = sum(gaps['role_gaps'].values()) + sum(gaps['quality_gaps'].values())
        
        return gaps
    
    def analyze_batting_order(self, team: Team) -> List[Dict[str, Any]]:
        """
        Analyze batting order based on player TAGS per AuctionPrompt Step h.
        
        Tag-based mapping (NOT hardcoded positions):
        - #Opener → Positions 1-2
        - #Top3Anchor → Positions 3-5
        - #MiddleOrder → Positions 3-6
        - #Finisher → Positions 6-7
        - #BattingOrder78 → Positions 7-8
        - Bowlers → Positions 8-11
        
        Status legend:
        - Check: Player assigned with Tier A quality
        - Adjusted: Player assigned with Tier B quality
        - NotCheck: Position unfilled (gap to be filled from auction supply)
        """
        playing11 = self.build_best_playing11(team)
        batting_order = []
        
        positions_needed = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        assigned_players = set()
        
        # Assign players based on their TAGS
        for pos in positions_needed:
            player_found = None
            player_tier = None
            speciality = None
            status = "NotCheck"
            
            # Position 1-2: #Opener tag
            if pos <= 2:
                for player in playing11:
                    if player not in assigned_players:
                        if hasattr(player, 'batting_tags') and '#Opener' in str(player.batting_tags):
                            player_found = player.name
                            player_tier = player.quality.value if player.quality else 'B'
                            speciality = '#Opener'
                            status = "Check" if player_tier == 'A' else "Adjusted"
                            assigned_players.add(player)
                            break
            
            # Position 3-5: #Top3Anchor or #MiddleOrder tags
            elif pos <= 5:
                for player in playing11:
                    if player not in assigned_players:
                        tags = str(player.batting_tags) if hasattr(player, 'batting_tags') else ""
                        if '#Top3Anchor' in tags or '#MiddleOrder' in tags:
                            player_found = player.name
                            player_tier = player.quality.value if player.quality else 'B'
                            speciality = '#Top3Anchor' if '#Top3Anchor' in tags else '#MiddleOrder'
                            status = "Check" if player_tier == 'A' else "Adjusted"
                            assigned_players.add(player)
                            break
            
            # Position 6-7: #Finisher or #BattingOrder456 or #BattingOrder67 tags
            elif pos <= 7:
                for player in playing11:
                    if player not in assigned_players:
                        tags = str(player.batting_tags) if hasattr(player, 'batting_tags') else ""
                        if '#Finisher' in tags or '#BattingOrder67' in tags or '#BattingOrder456' in tags:
                            player_found = player.name
                            player_tier = player.quality.value if player.quality else 'B'
                            speciality = '#Finisher'
                            status = "Check" if player_tier == 'A' else "Adjusted"
                            assigned_players.add(player)
                            break
            
            # Position 8-11: Bowlers (can be all-rounders with bowling capability)
            else:
                for player in playing11:
                    if player not in assigned_players:
                        if player.speciality and player.speciality.value in ['FastBowler', 'SpinBowler', 'BowlAR']:
                            player_found = player.name
                            player_tier = player.quality.value if player.quality else 'B'
                            speciality = player.speciality.value
                            status = "Check" if player_tier == 'A' else "Adjusted"
                            assigned_players.add(player)
                            break
            
            # Position unfilled
            if not player_found:
                player_found = "[OPEN]"
                speciality = self._get_batting_requirement_for_position(pos)
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
    
    def _get_batting_requirement_for_position(self, pos: int) -> str:
        """Get batting tag requirement for a position per AuctionPrompt Step h."""
        if pos <= 2:
            return '#Opener'
        elif pos <= 5:
            return '#Top3Anchor/#MiddleOrder'
        elif pos <= 7:
            return '#Finisher'
        else:
            return 'Bowler (FastBowler/SpinBowler)'
    
    def analyze_bowling_phases(self, team: Team) -> List[Dict[str, Any]]:
        """
        Analyze bowling phase coverage per AuctionPrompt Step i.
        
        Uses bowling TAGS to determine phase capability:
        - #PPBowler: Powerplay specialist
        - #MiddleOvers: Middle-overs specialist
        - #DeathOvers: Death-overs specialist
        
        Primary = Tier A bowlers with phase tag
        Backup = Tier B bowlers with phase tag OR any bowler in that speciality
        
        Status:
        - Check: ≥2 quality bowlers (Tier A) for phase
        - Adjusted: 1 Tier A OR ≥2 Tier B
        - NotCheck: <1 quality option (gap to fill from supply per AuctionPrompt Section E)
        """
        playing11 = self.build_best_playing11(team)
        phases = ['Powerplay', 'MiddleOvers', 'Death']
        bowling_analysis = []
        
        for phase in phases:
            primary_bowlers = []  # Tier A with phase tag
            backup_bowlers = []   # Tier B or less specific
            status = "NotCheck"
            
            for player in playing11:
                if not player.speciality or player.speciality.value not in ['FastBowler', 'SpinBowler', 'BowlAR']:
                    continue
                
                # Check for phase-specific tags
                has_phase_tag = False
                bowling_tags = str(player.bowling_tags) if hasattr(player, 'bowling_tags') else ""
                
                if phase == 'Powerplay':
                    has_phase_tag = '#PPBowler' in bowling_tags or '#RightArmFast' in bowling_tags or '#LeftArmPace' in bowling_tags
                elif phase == 'MiddleOvers':
                    has_phase_tag = '#MiddleOvers' in bowling_tags or '#Offspin' in bowling_tags or '#Legspin' in bowling_tags
                elif phase == 'Death':
                    has_phase_tag = '#DeathOvers' in bowling_tags or '#RightArmFast' in bowling_tags or '#LeftArmPace' in bowling_tags
                
                # Categorize as primary (Tier A) or backup (Tier B)
                if has_phase_tag:
                    if player.quality and player.quality.value == 'A':
                        primary_bowlers.append(player.name)
                    else:
                        backup_bowlers.append(player.name)
                elif player.speciality.value in ['FastBowler', 'SpinBowler']:
                    # Generic bowlers can serve as backup
                    if player.quality and player.quality.value == 'A':
                        backup_bowlers.append(player.name)
                    else:
                        backup_bowlers.append(player.name)
            
            # Determine status per AuctionPrompt
            if len(primary_bowlers) >= 2:
                status = "Check"
            elif len(primary_bowlers) >= 1 or len(backup_bowlers) >= 2:
                status = "Adjusted"
            else:
                status = "NotCheck"  # RED phase per Section E/F
            
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
        """
        Complete team analysis per AuctionPrompt.
        
        Outputs:
        - Playing 11: Best 11 from retained (quality-based, role-balanced)
        - Gaps: Role + Quality + Phase gaps to be filled from auction supply
        - Batting order: 11 positions mapped to player tags (#Opener, #MiddleOrder, #Finisher)
        - Bowling phases: Powerplay/Middle/Death coverage per phase tags
        
        Weak points identified for LLM recommender to address via auction buys.
        """
        playing11 = self.build_best_playing11(team)
        gaps = self.identify_gaps(team)
        batting_order = self.analyze_batting_order(team)
        bowling_phases = self.analyze_bowling_phases(team)
        
        # Identify weak points (gaps to fill from auction supply)
        weak_points = []
        
        # Check batting order gaps per Step h
        open_positions = [bo for bo in batting_order if bo['status'] == 'NotCheck']
        if open_positions:
            weak_points.append({
                'category': 'Batting Order',
                'severity': 'High',
                'details': f"Missing players for positions: {[bo['position'] for bo in open_positions]}",
                'required_tags': [bo['speciality'] for bo in open_positions]
            })
        
        # Check bowling phase gaps per Step i (RED phases)
        critical_phases = [bp for bp in bowling_phases if bp['status'] == 'NotCheck']
        if critical_phases:
            weak_points.append({
                'category': 'Bowling Phases (RED)',
                'severity': 'High',
                'demand_boost': '+3 per AuctionPrompt Section F',
                'details': f"Missing coverage for: {[bp['phase'] for bp in critical_phases]}",
                'required_tags': [f"#{bp['phase']}Bowler" for bp in critical_phases]
            })
        
        # Role-specific gaps
        role_gaps = gaps.get('role_gaps', {})
        if role_gaps['wk'] > 0:
            weak_points.append({
                'category': 'Wicket Keeper',
                'severity': 'Critical',
                'details': f"Missing {role_gaps['wk']} WK(s) in playing 11",
                'required_tags': ['#WK']
            })
        
        if role_gaps['opener'] > 0:
            weak_points.append({
                'category': 'Openers',
                'severity': 'High',
                'details': f"Need {role_gaps['opener']} more opener(s)",
                'required_tags': ['#Opener']
            })
        
        if role_gaps['finisher'] > 0:
            weak_points.append({
                'category': 'Finishers',
                'severity': 'Medium',
                'details': f"Need {role_gaps['finisher']} finisher(s)",
                'required_tags': ['#Finisher']
            })
        
        if role_gaps['pacer'] > 0:
            weak_points.append({
                'category': 'Pace Bowling',
                'severity': 'High',
                'details': f"Need {role_gaps['pacer']} more pacer(s)",
                'required_speciality': 'FastBowler'
            })
        
        if role_gaps['spinner'] > 0:
            weak_points.append({
                'category': 'Spin Bowling',
                'severity': 'Medium',
                'details': f"Need {role_gaps['spinner']} more spinner(s)",
                'required_speciality': 'SpinBowler'
            })
        
        # Tier A requirement lives under 'quality_gaps' in the gaps structure
        tier_a_needed = gaps.get('quality_gaps', {}).get('tier_a_needed', 0)
        if tier_a_needed > 0:
            weak_points.append({
                'category': 'Quality (Tier A)',
                'severity': 'Medium',
                'details': f"Target {tier_a_needed} more Tier A player(s) for ~50% quality",
                'required_quality': 'Tier A'
            })
        
        # Purse constraints (affects bid strategy per AuctionPrompt Section C/D)
        purse_available_cr = team.purse_available / 100.0
        if purse_available_cr < 10:
            weak_points.append({
                'category': 'Purse Constraint',
                'severity': 'Medium',
                'pivot': 'Pivot B: Value buys per AuctionPrompt',
                'details': f"Limited purse: {purse_available_cr:.2f} Cr remaining",
                'strategy': 'Focus on budget options (<base+50%)'
            })
        
        return {
            'team': team.name,
            'playing11': [p.name for p in playing11],
            'playing11_size': len(playing11),
            'gaps': gaps,
            'batting_order': batting_order,
            'bowling_phases': bowling_phases,
            'weak_points': weak_points,
            'total_players': team.total_players,
            'available_slots': team.available_slots,
            'purse_available': team.purse_available,
            'purse_available_cr': purse_available_cr
        }

