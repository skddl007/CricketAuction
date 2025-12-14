"""LLM-based team matcher with bias awareness and advanced metrics."""

from typing import Dict, Any, Optional, List, Tuple
from models.player import Player
from models.team import Team
from llm.gemini_client import GeminiClient
from llm.prompt_loader import PromptLoader
from core.bias_integrator import BiasIntegrator
from core.team_requirements import TeamRequirementsGenerator
from core.player_profile import PlayerProfileGenerator
import json
import re


class TeamMatcher:
    """Match players to teams using LLM reasoning."""
    
    def __init__(self, gemini_client: GeminiClient, bias_integrator: BiasIntegrator):
        """Initialize matcher."""
        self.client = gemini_client
        self.bias_integrator = bias_integrator
        self.requirements_generator = TeamRequirementsGenerator()
        self.profile_generator = PlayerProfileGenerator()
        self.prompt_loader = PromptLoader()
    
    def create_matching_prompt(
        self,
        player: Player,
        team: Team,
        requirements: Dict[str, Any],
        bias_context: str
    ) -> str:
        """Create prompt for LLM team matching."""
        player_profile = self.profile_generator.generate_profile(player)
        
        # Format advanced metrics
        metrics_str = "N/A"
        if player_profile.get('advanced_metrics'):
            am = player_profile['advanced_metrics']
            metrics_str = f"""
Powerplay: efscore={am['powerplay'].get('efscore', 'N/A')}, winp={am['powerplay'].get('winp', 'N/A')}, raa={am['powerplay'].get('raa', 'N/A')}
Middle Overs: efscore={am['middle_overs'].get('efscore', 'N/A')}, winp={am['middle_overs'].get('winp', 'N/A')}, raa={am['middle_overs'].get('raa', 'N/A')}
Death: efscore={am['death'].get('efscore', 'N/A')}, winp={am['death'].get('winp', 'N/A')}, raa={am['death'].get('raa', 'N/A')}
"""
        
        # Format conditions performance
        conditions_str = f"Balance Score: {player_profile.get('conditions_balance_score', 0):.2f}, Adaptability: {player_profile.get('conditions_adaptability', 0):.2f}"
        
        # Format requirements
        req_str = "\n".join([
            f"- {r['role']} ({r['urgency']}): {r['reason']}"
            for r in requirements.get('requirements', [])[:5]  # Top 5 requirements
        ])
        
        # Format retained players
        retained_str = ", ".join([p.name for p in team.retained_players[:10]])  # First 10
        
        # Load system context from AuctionPrompt.md
        system_context = self.prompt_loader.get_matching_context()
        
        # Get player's detailed tags if available
        player_tags = ""
        if hasattr(player, 'metadata'):
            detailed_batting = player.metadata.get('detailed_batting_tags', [])
            detailed_bowling = player.metadata.get('detailed_bowling_tags', [])
            if detailed_batting or detailed_bowling:
                player_tags = f"""
Player Tags:
- Batting: {', '.join(detailed_batting) if detailed_batting else 'N/A'}
- Bowling: {', '.join(detailed_bowling) if detailed_bowling else 'N/A'}
"""
        
        prompt = f"""{system_context}

=== TEAM-PLAYER MATCHING TASK ===

Follow Step f) framework from the instructions above to compute demand score and price ranges.

Player: {player.name}
Profile: {json.dumps(player_profile, indent=2)}
{player_tags}
Advanced Metrics:
{metrics_str}

Conditions Performance: {conditions_str}

Team: {team.name}
Home Ground: {team.home_ground} ({team.ground_condition})
Purse Available: {team.purse_available}L ({team.purse_available/100:.2f} Cr)
Available Slots: {team.available_slots}
Available Foreign Slots: {team.available_foreign_slots}

Team Requirements:
{req_str}

Retained Players: {retained_str}

{bias_context}

=== ANALYSIS REQUIREMENTS (Step f) Framework) ===

Compute a 0-10 demand score by combining:
1. Role fit: How well does this player fill team's gaps? (Consider batting order needs, bowling phase needs)
2. Quality gap: How does player quality match team needs? (Tier A/B alignment)
3. Purse flexibility: Can team afford this player? (Consider remaining purse and slots)
4. Overseas slot availability: Is foreign slot available if needed? (Max 8 foreigners in squad, 4 in playing XI)
5. Release history: Buy-back likelihood (teams rarely buy back released players unless specific skill needed or price drops)
6. Player-team synergy: Historical combos, captain/coach trust (but NOT if player was released from this team)

IMPORTANT CONSIDERATIONS:
- In small auctions, demand-supply gaps get amplified
- Define TWO price bands:
  * Fair price: Based on balanced squad building
  * All-out price: If player fills primary gap and rest can be Tier-B picks
- Consider behavioral patterns (Section C): Teams prioritize Indian core, overseas all-rounders get HIGH prices, etc.
- Consider spending trends (Section D): Overseas batters = LOW priority unless exceptional, etc.
- Weight factors: Batting orders (40%), Bowling phases (30%), Strategies (50%)

Respond in JSON format following Step f) output format:
{{
  "role_fit_score": 0-10,
  "quality_gap_score": 0-10,
  "home_ground_suitability": 0-10,
  "purse_flexibility": 0-10,
  "overseas_slot_availability": 0-10,
  "bias_factor": 0-10,
  "conditions_adaptability": 0-10,
  "release_history_factor": 0-10,
  "synergy_factor": 0-10,
  "overall_demand_score": 0-10,
  "fair_price_range": "X-Y",
  "all_out_price_range": "X-Y",
  "gaps_filled": ["gap1", "gap2"],
  "demand_reasoning": "Brief explanation of demand score calculation"
}}

Format the output similar to Step f) example:
Player Name: {player.name}
Tags: {', '.join(detailed_batting[:3]) if detailed_batting else 'N/A'}, {', '.join(detailed_bowling[:3]) if detailed_bowling else 'N/A'}
Speciality: [from player profile]
Quality Tier: [A or B]
{team.name} – Demand [X]/10 | Fair: [X-Y]Cr | All-out: [X-Y]Cr | Fills: [specific gaps]
"""
        return prompt
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data."""
        # Try to extract JSON
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        # Fallback
        try:
            return json.loads(response)
        except:
            return {}
    
    def match_player_to_team(
        self,
        player: Player,
        team: Team
    ) -> Dict[str, Any]:
        """Match a player to a team using LLM."""
        # Get requirements
        requirements = self.requirements_generator.generate_requirements(team)
        
        # Get bias context
        bias_context = self.bias_integrator.get_bias_context_for_llm(player.name, team.name)
        
        # Create prompt
        prompt = self.create_matching_prompt(player, team, requirements, bias_context)
        
        try:
            response = self.client.generate_content(prompt)
            match_result = self.parse_llm_response(response)
            
            # Add bias boost to demand score
            base_demand = match_result.get('overall_demand_score', 0)
            adjusted_demand = self.bias_integrator.add_bias_to_demand_score(
                base_demand,
                player.name,
                team.name
            )
            match_result['overall_demand_score'] = adjusted_demand
            match_result['base_demand_score'] = base_demand
            match_result['bias_boost'] = adjusted_demand - base_demand
            
            # Add metadata
            match_result['player_name'] = player.name
            match_result['team_name'] = team.name
            match_result['requirements'] = requirements
            
            # Add new fields from AuctionPrompt.md format
            match_result['release_history_factor'] = match_result.get('release_history_factor', 5.0)
            match_result['synergy_factor'] = match_result.get('synergy_factor', 5.0)
            match_result['demand_reasoning'] = match_result.get('demand_reasoning', '')
            
            return match_result
        except Exception as e:
            print(f"Error matching {player.name} to {team.name}: {e}")
            return {
                'player_name': player.name,
                'team_name': team.name,
                'overall_demand_score': 0,
                'error': str(e)
            }
    
    def match_player_to_all_teams(
        self,
        player: Player,
        teams: Dict[str, Team]
    ) -> List[Dict[str, Any]]:
        """Match a player to all teams."""
        matches = []
        for team_name, team in teams.items():
            match_result = self.match_player_to_team(player, team)
            matches.append(match_result)
        
        # Sort by demand score
        matches.sort(key=lambda x: x.get('overall_demand_score', 0), reverse=True)
        return matches

