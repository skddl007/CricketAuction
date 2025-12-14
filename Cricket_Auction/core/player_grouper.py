"""Player grouping system (A/B/C) based on fit quality and price range."""

from typing import Dict, List, Any, Tuple
from models.player import Player
from models.team import Team
from core.recommender import Recommender


class PlayerGrouper:
    """Group players into A, B, C categories."""
    
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
    
    def group_players(
        self,
        team: Team,
        recommendations: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group players into A, B, C categories."""
        groups = {
            'A': [],  # Perfect fit + High price
            'B': [],  # Good fit + Mid-range
            'C': []  # Backup + Budget
        }
        
        for rec in recommendations:
            demand_score = rec.get('overall_demand_score', 0)
            fair_price_str = rec.get('fair_price_range', '0-0')
            fair_price_min, fair_price_max = self.parse_price_range(fair_price_str)
            fair_price_avg = (fair_price_min + fair_price_max) / 2
            
            gaps_filled = rec.get('gaps_filled', [])
            is_primary_gap = any('critical' in str(g).lower() or 'wk' in str(g).lower() for g in gaps_filled)
            
            # Determine group
            if demand_score >= 8.0 and fair_price_avg >= 10 and is_primary_gap:
                # Group A: Perfect fit, high price, primary gap
                groups['A'].append(rec)
            elif demand_score >= 6.5 and fair_price_avg >= 5:
                # Group B: Good fit, mid-range
                groups['B'].append(rec)
            else:
                # Group C: Backup, budget
                groups['C'].append(rec)
        
        # Sort each group by demand score
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
            f"Team: {team.name}",
            f"Purse: {team.purse_available / 100:.1f} Cr | Slots: {team.available_slots}",
            ""
        ]
        
        # Group A
        if groups['A']:
            lines.append("Group A (Perfect Fit - High Priority):")
            for rec in groups['A'][:5]:  # Top 5
                player_name = rec.get('player_name', 'Unknown')
                demand = rec.get('overall_demand_score', 0)
                fair_price = rec.get('fair_price_range', 'N/A')
                gaps = ", ".join(rec.get('gaps_filled', [])[:2])
                lines.append(f"  - {player_name}: Demand {demand:.1f}/10 | Fair: {fair_price}Cr | Fills: {gaps}")
            lines.append("")
        
        # Group B
        if groups['B']:
            lines.append("Group B (Good Fit - Mid Range):")
            for rec in groups['B'][:5]:  # Top 5
                player_name = rec.get('player_name', 'Unknown')
                demand = rec.get('overall_demand_score', 0)
                fair_price = rec.get('fair_price_range', 'N/A')
                gaps = ", ".join(rec.get('gaps_filled', [])[:2])
                lines.append(f"  - {player_name}: Demand {demand:.1f}/10 | Fair: {fair_price}Cr | Fills: {gaps}")
            lines.append("")
        
        # Group C
        if groups['C']:
            lines.append("Group C (Backup Options - Budget):")
            for rec in groups['C'][:5]:  # Top 5
                player_name = rec.get('player_name', 'Unknown')
                demand = rec.get('overall_demand_score', 0)
                fair_price = rec.get('fair_price_range', 'N/A')
                gaps = ", ".join(rec.get('gaps_filled', [])[:2])
                lines.append(f"  - {player_name}: Demand {demand:.1f}/10 | Fair: {fair_price}Cr | Fills: {gaps}")
        
        return "\n".join(lines)
    
    def get_grouped_recommendations(
        self,
        team: Team,
        available_players: List[Player],
        limit_per_group: int = 5
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Get grouped recommendations for a team."""
        print(f"[PLAYER_GROUPER] get_grouped_recommendations called")
        print(f"[PLAYER_GROUPER] Team: {team.name if team else 'None'}")
        print(f"[PLAYER_GROUPER] Available players: {len(available_players)}")
        print(f"[PLAYER_GROUPER] Limit per group: {limit_per_group}")
        print(f"[PLAYER_GROUPER] Recommender exists: {self.recommender is not None}")
        
        if not self.recommender:
            print("[PLAYER_GROUPER] ERROR: Recommender is None!")
            return {'A': [], 'B': [], 'C': []}
        
        # Get recommendations
        print("[PLAYER_GROUPER] Getting recommendations from recommender...")
        recommendations = self.recommender.recommend_for_team(team, available_players, limit=30)
        print(f"[PLAYER_GROUPER] Received {len(recommendations)} recommendations")
        
        if not recommendations:
            print("[PLAYER_GROUPER] WARNING: No recommendations received!")
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

