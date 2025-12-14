"""Recommendation engine with formatted output."""

from typing import Dict, List, Any, Optional
from models.player import Player
from models.team import Team
from llm.team_matcher import TeamMatcher
from core.bias_integrator import BiasIntegrator


class Recommender:
    """Generate player recommendations for teams."""
    
    def __init__(self, team_matcher: TeamMatcher):
        """Initialize recommender."""
        self.team_matcher = team_matcher
    
    def recommend_player(self, player: Player, teams: Dict[str, Team]) -> str:
        """Generate recommendation string for a player."""
        matches = self.team_matcher.match_player_to_all_teams(player, teams)
        
        # Format player info
        lines = [
            f"=== {player.name} ===",
            f"Country: {player.country} | Base Price: {player.base_price}L"
        ]
        
        # Tags
        tags = []
        if player.primary_role:
            tags.append(player.primary_role.value)
        if player.speciality:
            tags.append(player.speciality.value)
        if player.quality:
            tags.append(f"Tier {player.quality.value}")
        if tags:
            lines.append(f"Tags: {', '.join(tags)}")
        
        # Advanced metrics
        if player.advanced_metrics:
            pp = player.advanced_metrics.powerplay or {}
            mo = player.advanced_metrics.middle_overs or {}
            death = player.advanced_metrics.death or {}
            lines.append(
                f"Advanced Metrics: "
                f"efscore(PP/MO/Death)={pp.get('efscore', 'N/A')}/{mo.get('efscore', 'N/A')}/{death.get('efscore', 'N/A')}, "
                f"winp(PP/MO/Death)={pp.get('winp', 'N/A')}/{mo.get('winp', 'N/A')}/{death.get('winp', 'N/A')}, "
                f"raa(PP/MO/Death)={pp.get('raa', 'N/A')}/{mo.get('raa', 'N/A')}/{death.get('raa', 'N/A')}"
            )
        
        # Conditions
        balance_score = player.get_conditions_balance_score()
        if balance_score > 0.6:
            lines.append(f"Conditions: Balanced (score: {balance_score:.2f})")
        else:
            lines.append(f"Conditions: Needs specific conditions (score: {balance_score:.2f})")
        
        lines.append("")
        
        # Team recommendations
        for match in matches[:5]:  # Top 5 teams
            if match.get('error'):
                continue
            
            team_name = match['team_name']
            demand = match.get('overall_demand_score', 0)
            fair_price = match.get('fair_price_range', 'N/A')
            all_out_price = match.get('all_out_price_range', 'N/A')
            gaps_filled = match.get('gaps_filled', [])
            bias_boost = match.get('bias_boost', 0)
            
            # Format gaps
            gaps_str = ", ".join(gaps_filled[:3]) if gaps_filled else "General fit"
            
            # Format bias
            bias_str = ""
            if bias_boost > 0.1:
                bias_str = f" | Bias: +{bias_boost:.1f}"
            
            lines.append(
                f"{team_name} – Demand {demand:.1f}/10 | "
                f"Fair: {fair_price}Cr | "
                f"All-out: {all_out_price}Cr | "
                f"Fills: {gaps_str}{bias_str}"
            )
        
        return "\n".join(lines)
    
    def recommend_for_team(
        self,
        team: Team,
        available_players: List[Player],
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get recommendations for a specific team."""
        recommendations = []
        
        for player in available_players:
            match_result = self.team_matcher.match_player_to_team(player, team)
            if not match_result.get('error'):
                recommendations.append(match_result)
        
        # Sort by demand score
        recommendations.sort(key=lambda x: x.get('overall_demand_score', 0), reverse=True)
        
        return recommendations[:limit]

