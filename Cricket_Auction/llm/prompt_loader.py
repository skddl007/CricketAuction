"""Load and manage system prompts from AuctionPrompt.md."""

from pathlib import Path
from typing import Optional


class PromptLoader:
    """Load system prompts from AuctionPrompt.md."""
    
    def __init__(self, prompt_file: Optional[str] = None):
        """Initialize prompt loader."""
        if prompt_file is None:
            # Default to AuctionPrompt.md in the project root
            project_root = Path(__file__).parent.parent
            self.prompt_file = project_root / "AuctionPrompt.md"
        else:
            self.prompt_file = Path(prompt_file)
        self._cached_prompt: Optional[str] = None
    
    def load_prompt(self) -> str:
        """Load the full prompt from AuctionPrompt.md."""
        if self._cached_prompt is not None:
            return self._cached_prompt
        
        try:
            if self.prompt_file.exists():
                with open(self.prompt_file, 'r', encoding='utf-8') as f:
                    self._cached_prompt = f.read()
            else:
                # Fallback if file doesn't exist
                self._cached_prompt = self._get_default_prompt()
        except Exception as e:
            print(f"Warning: Could not load AuctionPrompt.md: {e}")
            self._cached_prompt = self._get_default_prompt()
        
        return self._cached_prompt
    
    def get_tagging_context(self) -> str:
        """Get the relevant context for player tagging (Step a, b, c)."""
        full_prompt = self.load_prompt()
        
        # Extract Step a, b, c sections
        context = """You are an IPL auction strategist. Follow these instructions for player tagging:

"""
        
        # Extract Step a
        if "Step a)" in full_prompt:
            step_a_start = full_prompt.find("Step a)")
            step_b_start = full_prompt.find("Step b)")
            if step_b_start > step_a_start:
                context += full_prompt[step_a_start:step_b_start].strip() + "\n\n"
        
        # Extract Step b
        if "Step b)" in full_prompt:
            step_b_start = full_prompt.find("Step b)")
            step_c_start = full_prompt.find("Step c)")
            if step_c_start > step_b_start:
                context += full_prompt[step_b_start:step_c_start].strip() + "\n\n"
        
        # Extract Step c
        if "Step c)" in full_prompt:
            step_c_start = full_prompt.find("Step c)")
            step_d_start = full_prompt.find("Step d)")
            if step_d_start > step_c_start:
                context += full_prompt[step_c_start:step_d_start].strip() + "\n\n"
        
        # Add data sources note
        if "A) Data Sources:" in full_prompt:
            data_sources_start = full_prompt.find("A) Data Sources:")
            data_sources_end = full_prompt.find("B) Auction Rules", data_sources_start)
            if data_sources_end > data_sources_start:
                context += "\n" + full_prompt[data_sources_start:data_sources_end].strip() + "\n"
        
        return context
    
    def get_matching_context(self) -> str:
        """Get the relevant context for team matching (Step f, behavioral patterns, spending trends)."""
        full_prompt = self.load_prompt()
        
        context = """You are an IPL auction strategist. Follow these instructions for team-player matching:

"""
        
        # Extract Step f
        if "Step f)" in full_prompt:
            step_f_start = full_prompt.find("Step f)")
            step_g_start = full_prompt.find("Step g)")
            if step_g_start > step_f_start:
                context += full_prompt[step_f_start:step_g_start].strip() + "\n\n"
            elif step_g_start == -1:
                # Step g not found, take until end or next section
                step_h_start = full_prompt.find("Step h)", step_f_start)
                if step_h_start > step_f_start:
                    context += full_prompt[step_f_start:step_h_start].strip() + "\n\n"
        
        # Extract Behavioral patterns (Section C)
        if "C) Behavioural pattern" in full_prompt:
            behavior_start = full_prompt.find("C) Behavioural pattern")
            behavior_end = full_prompt.find("D) Some Auction spending", behavior_start)
            if behavior_end > behavior_start:
                context += "\n" + full_prompt[behavior_start:behavior_end].strip() + "\n\n"
        
        # Extract Spending trends (Section D)
        if "D) Some Auction spending trends" in full_prompt:
            spending_start = full_prompt.find("D) Some Auction spending trends")
            spending_end = full_prompt.find("E) Batting orders", spending_start)
            if spending_end > spending_start:
                context += "\n" + full_prompt[spending_start:spending_end].strip() + "\n\n"
        
        # Extract weighted factors (E, F, G)
        if "E) Batting orders" in full_prompt:
            e_start = full_prompt.find("E) Batting orders")
            e_end = full_prompt.find("F) Bowling phases", e_start)
            if e_end > e_start:
                context += "\n" + full_prompt[e_start:e_end].strip() + "\n"
        
        if "F) Bowling phases" in full_prompt:
            f_start = full_prompt.find("F) Bowling phases")
            f_end = full_prompt.find("G) Strategies", f_start)
            if f_end > f_start:
                context += "\n" + full_prompt[f_start:f_end].strip() + "\n"
        
        if "G) Strategies" in full_prompt:
            g_start = full_prompt.find("G) Strategies")
            context += "\n" + full_prompt[g_start:].strip() + "\n"
        
        # Add auction rules
        if "B) Auction Rules" in full_prompt:
            rules_start = full_prompt.find("B) Auction Rules")
            rules_end = full_prompt.find("C) Behavioural pattern", rules_start)
            if rules_end > rules_start:
                context += "\n" + full_prompt[rules_start:rules_end].strip() + "\n"
        
        return context
    
    def get_full_context(self) -> str:
        """Get the full prompt context."""
        return self.load_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default prompt if file is not found."""
        return """You are an IPL auction strategist running a simulation model.
Your goal is to analyze players and match them to teams based on comprehensive data analysis."""
    
    def clear_cache(self):
        """Clear the cached prompt."""
        self._cached_prompt = None

