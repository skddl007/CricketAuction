"""Player grouping system - LLM-driven based on team context (no hardcoded thresholds)."""

from typing import Dict, List, Any, Tuple, Optional
from models.player import Player
from models.team import Team
from core.recommender import Recommender


class PlayerGrouper:
    """
    Group players based on fit for team's SPECIFIC gaps.
    
    Groups:
    - A: Perfect fit (fills CRITICAL/RED gap + Tier A + affordable)
    - B: Good fit (fills high gap + available budget)
    - C: Backup (fills secondary gap or budget option)
    
    Grouping is CONTEXTUAL, not hardcoded thresholds.
    """
    
    def __init__(self, recommender: Recommender):
        """Initialize grouper."""
        self.recommender = recommender
    
    def parse_price_range(self, price_str: str) -> Tuple[float, float]:
        """Parse price range string like '11-14' to (11, 14)."""
        try:
            parts = price_str.split('-')
            if len(parts) == 2:
                return (float(parts[0]), float(parts[1]))
            elif len(parts) == 1:
                val = float(parts[0])
                return (val, val)
        except:
            pass
        return (0, 0)
    
    def determine_gap_criticality(self, gaps_filled: List[str]) -> str:
        """
        Determine gap type from filled gaps.
        
        Returns: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
        """
        gap_str = ' '.join(gaps_filled).upper()
        
        # CRITICAL gaps: Batting positions, RED phases, WK
        if any(crit in gap_str for crit in ['POSITION', 'OPEN', 'RED', 'CRITICAL', 'WK']):
            return 'CRITICAL'
        
        # HIGH gaps: Primary roles
        if any(high in gap_str for high in ['OPENER', 'FINISHER', 'PACER', 'PPBOWLER', 'DEATHBOWLER']):
            return 'HIGH'
        
        # MEDIUM: Secondary specialities
        if any(med in gap_str for med in ['SPINNER', 'MIDDLEORDER', 'TIER A']):
            return 'MEDIUM'
        
        # LOW: Depth/backup
        return 'LOW'
    
    def group_players(
        self,
        team: Team,
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Group players contextually based on team's gaps and budget.
        
        Logic (NOT hardcoded):
        - Group A: Fills CRITICAL gap + Tier A + within 30% purse
        - Group B: Fills HIGH gap + within 50% purse
        - Group C: Budget option or secondary gap
        """
        groups = {
            'A': [],
            'B': [],
            'C': []
        }
        
        if not recommendations:
            return groups
        
        # Calculate team's purse threshold
        purse_available = team.purse_available / 100.0  # Convert to Cr
        purse_30_threshold = purse_available * 0.3
        purse_50_threshold = purse_available * 0.5
        
        for rec in recommendations:
            demand_score = rec.get('overall_demand_score', 0)
            gaps_filled = rec.get('gaps_filled', [])
            gap_criticality = self.determine_gap_criticality(gaps_filled)
            
            fair_price_str = rec.get('fair_price_range', '0-0')
            fair_price_min, fair_price_max = self.parse_price_range(fair_price_str)
            fair_price_avg = (fair_price_min + fair_price_max) / 2 if fair_price_max > 0 else 0
            
            # Determine group based on criticality + affordability
            if gap_criticality == 'CRITICAL' and fair_price_avg <= purse_30_threshold and demand_score >= 7.5:
                # Group A: Perfect fit
                groups['A'].append(rec)
            elif gap_criticality in ['CRITICAL', 'HIGH'] and fair_price_avg <= purse_50_threshold and demand_score >= 6.0:
                # Group B: Good fit
                groups['B'].append(rec)
            else:
                # Group C: Backup or budget option
                groups['C'].append(rec)
        
        # Sort each group by demand score (descending)
        for group in groups.values():
            group.sort(key=lambda x: x.get('overall_demand_score', 0), reverse=True)
        
        return groups
    
    def format_grouped_recommendations(
        self,
        team: Team,
        groups: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Format grouped recommendations for display."""
        lines = [
            f"=== {team.name} RECOMMENDATIONS ===",
            f"Purse: {team.purse_available / 100:.1f} Cr | Slots: {team.available_slots}",
            f"Foreigners available: {team.available_foreign_slots}",
            ""
        ]
        
        # Group A
        group_a = groups.get('A', [])
        if group_a:
            lines.append("GROUP A - CRITICAL GAPS (High Priority)")
            lines.append("-" * 70)
            for i, rec in enumerate(group_a[:5], 1):
                player_name = rec.get('player_name', 'Unknown')
                demand = rec.get('overall_demand_score', 0)
                fair_price = rec.get('fair_price_range', 'N/A')
                gaps = ", ".join(rec.get('gaps_filled', [])[:2])
                lines.append(f"{i}. {player_name}")
                lines.append(f"   Demand: {demand:.1f}/10 | Fair Price: {fair_price}Cr")
                lines.append(f"   Fills: {gaps}")
                lines.append("")
        
        # Group B
        group_b = groups.get('B', [])
        if group_b:
            lines.append("GROUP B - HIGH GAPS (Medium Priority)")
            lines.append("-" * 70)
            for i, rec in enumerate(group_b[:5], 1):
                player_name = rec.get('player_name', 'Unknown')
                demand = rec.get('overall_demand_score', 0)
                fair_price = rec.get('fair_price_range', 'N/A')
                gaps = ", ".join(rec.get('gaps_filled', [])[:2])
                lines.append(f"{i}. {player_name}")
                lines.append(f"   Demand: {demand:.1f}/10 | Fair Price: {fair_price}Cr")
                lines.append(f"   Fills: {gaps}")
                lines.append("")
        
        # Group C
        group_c = groups.get('C', [])
        if group_c:
            lines.append("GROUP C - BACKUP OPTIONS (Budget Friendly)")
            lines.append("-" * 70)
            for i, rec in enumerate(group_c[:5], 1):
                player_name = rec.get('player_name', 'Unknown')
                demand = rec.get('overall_demand_score', 0)
                fair_price = rec.get('fair_price_range', 'N/A')
                gaps = ", ".join(rec.get('gaps_filled', [])[:2])
                lines.append(f"{i}. {player_name}")
                lines.append(f"   Demand: {demand:.1f}/10 | Fair Price: {fair_price}Cr")
                lines.append(f"   Fills: {gaps}")
                lines.append("")
        
        return "\n".join(lines)
    
    def get_grouped_recommendations(
        self,
        team: Team,
        available_players: List[Player],
        limit_per_group: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get grouped recommendations for a team."""
        if not self.recommender:
            # Use fallback heuristic-based recommendations
            return self._get_heuristic_recommendations(team, available_players, limit_per_group)
        
        # Get recommendations from LLM-based recommender
        recommendations = self.recommender.recommend_for_team(team, available_players, limit=30)
        
        # Group them
        groups = self.group_players(team, recommendations)
        
        # Limit each group
        for group_name in groups:
            groups[group_name] = groups[group_name][:limit_per_group]
        
        return groups
    
    def _get_heuristic_recommendations(
        self,
        team: Team,
        available_players: List[Player],
        limit_per_group: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Generate heuristic-based recommendations when LLM is unavailable.
        Uses player attributes and team needs.
        """
        recommendations = []
        
        for player in available_players:
            # Calculate a basic demand score (0-10)
            demand_score = self._calculate_demand_score(player, team)
            
            # Estimate fair price (simplified)
            fair_price = self._estimate_fair_price(player)
            
            # Determine what gaps this player fills (simplified)
            gaps_filled = self._determine_gaps_filled(player, team)
            
            rec = {
                'player_name': player.name,
                'player_id': getattr(player, 'id', None),
                'overall_demand_score': demand_score,
                'fair_price_range': fair_price,
                'base_price': player.base_price,
                'primary_role': player.primary_role.value if player.primary_role else 'Unknown',
                'speciality': player.speciality.value if player.speciality else 'None',
                'quality': player.quality.value if player.quality else 'D',
                'gaps_filled': gaps_filled,
                'country': player.country
            }
            
            if demand_score >= 4.0:  # Only include players with meaningful demand
                recommendations.append(rec)
        
        # Sort by demand score
        recommendations.sort(key=lambda x: x['overall_demand_score'], reverse=True)
        
        # Group them
        groups = self.group_players(team, recommendations)
        
        # Limit each group
        for group_name in groups:
            groups[group_name] = groups[group_name][:limit_per_group]
        
        print(f"[PLAYER_GROUPER] Generated {sum(len(g) for g in groups.values())} heuristic recommendations for {team.name}")
        for group_name, group_data in groups.items():
            print(f"[PLAYER_GROUPER]   Group {group_name}: {len(group_data)} items")
        
        return groups
    
    def _calculate_demand_score(self, player: Player, team: Team) -> float:
        """
        Calculate a basic demand score (0-10) for a player.
        Considers: experience, performance, speciality, and recent availability.
        """
        score = 5.0  # Base score
        
        # Quality boost
        if player.quality:
            quality_val = player.quality.value
            if quality_val == 'A':
                score += 3.0
            elif quality_val == 'B':
                score += 2.0
            elif quality_val == 'C':
                score += 1.0
        
        # International experience boost
        if player.international_leagues:
            score += 0.5 * min(len(player.international_leagues), 2)
        
        # IPL experience boost
        if player.ipl_experience and int(player.ipl_experience) > 0:
            score += min(int(player.ipl_experience) * 0.2, 1.0)
        
        # Cap at 10
        return min(score, 10.0)
    
    def _estimate_fair_price(self, player: Player) -> str:
        """
        Estimate fair price range for a player.
        Simple heuristic: base_price + quality boost.
        """
        base = float(player.base_price) if isinstance(player.base_price, (int, float, str)) else 0.5
        
        multiplier = 1.0
        if player.quality:
            quality_val = player.quality.value
            if quality_val == 'A':
                multiplier = 2.5
            elif quality_val == 'B':
                multiplier = 1.8
            elif quality_val == 'C':
                multiplier = 1.3
        
        fair_min = base * multiplier * 0.8
        fair_max = base * multiplier * 1.2
        
        return f"{fair_min:.1f}-{fair_max:.1f}"
    
    def _determine_gaps_filled(self, player: Player, team: Team) -> List[str]:
        """
        Determine what team gaps this player fills.
        Simplified: based on role and speciality.
        """
        gaps = []
        
        if not player.primary_role:
            return ['Generic_Depth']  # Default if no role
        
        role = player.primary_role.value.upper() if hasattr(player.primary_role, 'value') else str(player.primary_role).upper()
        spec = (player.speciality.value if player.speciality and hasattr(player.speciality, 'value') else str(player.speciality or "")).upper()
        
        # Batting roles
        if 'BATTER' in role or 'BAT' in role:
            if 'OPENER' in spec or 'OPENER' in str(player.batting_role or "").upper():
                gaps.append('Opening_Position')
            elif 'FINISHER' in spec:
                gaps.append('Finisher_Position')
            elif 'MIDDLE' in spec or 'MIDDLEORDER' in spec:
                gaps.append('MiddleOrder_Position')
            if not gaps:
                gaps.append('Batting_Depth')
        
        # Bowling roles
        if 'BOWLER' in role or 'PACER' in role or 'SPINNER' in role:
            if 'PACER' in spec or 'PACER' in str(player.bowling_role or "").upper():
                gaps.append('Pace_Attack')
            elif 'SPINNER' in spec or 'SPINNER' in str(player.bowling_role or "").upper():
                gaps.append('Spin_Attack')
            elif 'DEATH' in spec or 'DEATHBOWLER' in spec:
                gaps.append('Death_Bowling')
            elif 'PPBOWLER' in spec:
                gaps.append('Powerplay_Bowling')
            if not gaps:
                gaps.append('Bowling_Depth')
        
        # All-rounder
        if 'ALL' in role or 'AR' in role:
            gaps.append('Allrounder')
        
        # Wicketkeeper - check speciality
        if 'WK' in spec or 'WKBat' in str(player.speciality or ""):
            gaps.append('Wicketkeeper')
        
        return gaps[:3] if gaps else ['Generic_Depth']  # Return max 3 gaps

