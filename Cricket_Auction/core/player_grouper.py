"""Player grouping system - LLM-driven based on team context (no hardcoded thresholds)."""

from typing import Dict, List, Any, Tuple
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
        if groups['A']:
            lines.append("GROUP A - CRITICAL GAPS (High Priority)")
            lines.append("-" * 70)
            for i, rec in enumerate(groups['A'][:5], 1):
                player_name = rec.get('player_name', 'Unknown')
                demand = rec.get('overall_demand_score', 0)
                fair_price = rec.get('fair_price_range', 'N/A')
                gaps = ", ".join(rec.get('gaps_filled', [])[:2])
                lines.append(f"{i}. {player_name}")
                lines.append(f"   Demand: {demand:.1f}/10 | Fair Price: {fair_price}Cr")
                lines.append(f"   Fills: {gaps}")
                lines.append("")
        
        # Group B
        if groups['B']:
            lines.append("GROUP B - HIGH GAPS (Medium Priority)")
            lines.append("-" * 70)
            for i, rec in enumerate(groups['B'][:5], 1):
                player_name = rec.get('player_name', 'Unknown')
                demand = rec.get('overall_demand_score', 0)
                fair_price = rec.get('fair_price_range', 'N/A')
                gaps = ", ".join(rec.get('gaps_filled', [])[:2])
                lines.append(f"{i}. {player_name}")
                lines.append(f"   Demand: {demand:.1f}/10 | Fair Price: {fair_price}Cr")
                lines.append(f"   Fills: {gaps}")
                lines.append("")
        
        # Group C
        if groups['C']:
            lines.append("GROUP C - BACKUP OPTIONS (Budget Friendly)")
            lines.append("-" * 70)
            for i, rec in enumerate(groups['C'][:5], 1):
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
            return {'A': [], 'B': [], 'C': []}
        
        # Get recommendations
        recommendations = self.recommender.recommend_for_team(team, available_players, limit=30)
        
        # Group them
        groups = self.group_players(team, recommendations)
        
        return groups
        
        if not recommendations:
            print("[PLAYER_GROUPER] WARNING: No valid recommendations received!")
            return {'A': [], 'B': [], 'C': []}
        
        # Group them
        print("[PLAYER_GROUPER] Grouping recommendations...")
        groups = self.group_players(team, recommendations)
        print(f"[PLAYER_GROUPER] Groups created: {list(groups.keys())}")
        for group_name, group_data in groups.items():
            count = len(group_data) if isinstance(group_data, list) else 0
            print(f"[PLAYER_GROUPER]   Group {group_name}: {count} items before limiting")
        
        # Limit each group
        for group_name in groups:
            groups[group_name] = groups[group_name][:limit_per_group]
            print(f"[PLAYER_GROUPER]   Group {group_name}: {len(groups[group_name])} items after limiting")
        
        total = sum(len(g) if isinstance(g, list) else 0 for g in groups.values())
        print(f"[PLAYER_GROUPER] Total recommendations in groups: {total}")
        
        return groups

