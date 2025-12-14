"""Bias integrator to add bias scores to demand scoring and LLM prompts."""

from typing import Dict, Optional, Any
from core.bias_modeler import BiasModeler


class BiasIntegrator:
    """Integrate bias scores into demand scoring and LLM prompts."""
    
    def __init__(self, bias_modeler: BiasModeler):
        """Initialize integrator."""
        self.bias_modeler = bias_modeler
    
    def add_bias_to_demand_score(self, base_demand_score: float, player_name: str, team_name: str) -> float:
        """Add bias boost to demand score."""
        bias_score = self.bias_modeler.get_bias_score(player_name, team_name)
        
        # Add bias boost (0-1 scale, weighted)
        bias_boost = bias_score * 0.2  # Max 20% boost
        
        adjusted_score = base_demand_score + bias_boost
        return min(adjusted_score, 10.0)  # Cap at 10
    
    def get_bias_context_for_llm(self, player_name: str, team_name: str) -> str:
        """Get bias context string for LLM prompts."""
        bias_score = self.bias_modeler.get_bias_score(player_name, team_name)
        bias_reason = self.bias_modeler.get_bias_reason(player_name, team_name)
        
        if bias_score > 0.3:
            return f"Bias Factor: This player has historically performed exceptionally well against {team_name}. {bias_reason}. Bias Score: {bias_score:.2f}/1.0. This may influence the team's bidding behavior."
        elif bias_score > 0.1:
            return f"Bias Factor: This player has shown good performance against {team_name}. Bias Score: {bias_score:.2f}/1.0."
        else:
            return "Bias Factor: No significant historical bias detected."
    
    def format_bias_for_recommendation(self, player_name: str, team_name: str) -> str:
        """Format bias information for recommendation output."""
        bias_score = self.bias_modeler.get_bias_score(player_name, team_name)
        
        if bias_score > 0.5:
            return f"Bias: +{bias_score:.1f} (Strong)"
        elif bias_score > 0.3:
            return f"Bias: +{bias_score:.1f} (Moderate)"
        elif bias_score > 0.1:
            return f"Bias: +{bias_score:.1f} (Weak)"
        else:
            return ""

