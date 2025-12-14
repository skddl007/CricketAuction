"""LLM-based player tagging system using Gemini."""

from typing import Dict, Any, Optional, List
from models.player import Player, PrimaryRole, BattingRole, BowlingRole, Speciality, Quality
from llm.gemini_client import GeminiClient
from llm.prompt_loader import PromptLoader
import json
import re


class PlayerTagger:
    """Tag players using LLM analysis."""
    
    def __init__(self, gemini_client: GeminiClient):
        """Initialize tagger."""
        self.client = gemini_client
        self.prompt_loader = PromptLoader()
    
    def create_tagging_prompt(self, player: Player, stats_data: Optional[Dict[str, Any]] = None) -> str:
        """Create prompt for LLM player tagging using AuctionPrompt.md."""
        # Load system context from AuctionPrompt.md
        system_context = self.prompt_loader.get_tagging_context()
        
        # Build advanced metrics string
        metrics_str = "N/A"
        if player.advanced_metrics:
            pp = player.advanced_metrics.powerplay or {}
            mo = player.advanced_metrics.middle_overs or {}
            death = player.advanced_metrics.death or {}
            metrics_str = f"""
Advanced Metrics:
- Powerplay: efscore={pp.get('efscore', 'N/A')}, winp={pp.get('winp', 'N/A')}, raa={pp.get('raa', 'N/A')}
- Middle Overs: efscore={mo.get('efscore', 'N/A')}, winp={mo.get('winp', 'N/A')}, raa={mo.get('raa', 'N/A')}
- Death: efscore={death.get('efscore', 'N/A')}, winp={death.get('winp', 'N/A')}, raa={death.get('raa', 'N/A')}
"""
        
        # Build conditions performance string
        conditions_str = "N/A"
        if player.performance_by_conditions:
            conditions_str = f"Performance by conditions: {json.dumps(player.performance_by_conditions, indent=2)}"
        
        # Build stats string
        stats_str = ""
        if stats_data:
            stats_str = f"\nAdditional Stats: {json.dumps(stats_data, indent=2)}"
        
        prompt = f"""{system_context}

=== PLAYER ANALYSIS TASK ===

Using the instructions from AuctionPrompt.md above, analyze this cricket player and assign comprehensive tags following Step a), b), and c):

Player: {player.name}
Country: {player.country}
Batting Hand: {player.batting_hand or 'Unknown'}
Bowling Style: {player.bowling_style or 'N/A'}
Base Price: {player.base_price}L

{metrics_str}

Match Conditions Performance:
{conditions_str}
{stats_str}

=== ASSIGNMENT REQUIREMENTS ===

Based on Step a) - Assign detailed batting and bowling tags:
- Detailed batting tags (if applicable): Use hashtag format like #Opener, #Top3Anchor, #MiddleOrder, #Finisher, #PowerHitter, #SpinHitter, #PlaysPaceWell, #PlaysSpinWell, #WK, #BattingOrder456, etc.
- Detailed bowling tags (if applicable): Use hashtag format like #PPBowler, #MiddleOvers, #DeathOvers, #CanBowl4Overs, #2OverPartTimer, #RightArmFast, #LeftArmPace, #Legspin, #Offspin, #LeftArmOrthodox, #MysterySpinner, etc.
- Reference the CSK examples provided in the instructions for tag format

Based on Step b) - Classify into exactly one speciality category:
- Classify as: Batter, BatAR (bat-dominant AR, ≤2 overs), BowlAR (bowl-dominant AR, 2-4 overs), SpinBowler, or FastBowler
- Also specify if Indian or Foreigner (10 specialities total: 5 types × 2 nationalities)
- Follow the specific criteria for each category from Step b)

Based on Step c) - Assign Quality Tier:
- Tier A: First-choice for country/franchise OR clearly strong in a defined T20 role (proven IPL record or strong recent form) OR salary >=3Cr OR featured in teams scorecard 8/10 times in last year
- Tier B: Backup option, undefined role, limited sample, or average record (anything other than Tier A)

ADDITIONAL REQUIREMENT - Estimate Advanced Metrics (Phase-wise):
Based on the player analysis from AuctionPrompt.md above, estimate phase-wise metrics:
- **efscore** (Expected Runs vs Actual): 0-200, where 100 = average
  * Powerplay: 100-150 for openers/PP specialists, 80-120 for others
  * Middle Overs: 100-140 for middle-order/anchors, 80-120 for others
  * Death: 100-160 for finishers/death specialists, 80-120 for others
- **winp** (Win Probability Added): 0.0-1.0, where 0.5 = neutral
  * Powerplay: 0.4-0.6 for specialists, 0.45-0.55 for others
  * Middle Overs: 0.45-0.65 for key players, 0.45-0.55 for others
  * Death: 0.5-0.7 for finishers, 0.45-0.55 for others
- **raa** (Runs Above Average): Typically -20 to +30
  * Powerplay: +5 to +15 for good openers, -5 to +5 for others
  * Middle Overs: +5 to +20 for strong middle-order, -5 to +5 for others
  * Death: +10 to +25 for finishers, -5 to +5 for others

Estimate based on: Tier A = higher metrics, Tier B = average, Role-specific strengths

Respond in JSON format:
{{
  "primary_role": "Batter|BatAR|BowlAR|SpinBowler|FastBowler",
  "nationality_classification": "Indian|Foreigner",
  "batting_role": "Opener|MiddleOrder|Finisher",
  "bowling_role": "Pacer|WristSpinner|FingerSpinner|LeftArmSpinner|LegSpin|OffSpin|MysterySpinner|N/A",
  "speciality": "WKBat|PPBowler|MOBowler|DeathBowler|N/A",
  "detailed_batting_tags": ["#Opener", "#PowerHitter", ...],
  "detailed_bowling_tags": ["#PPBowler", "#CanBowl4Overs", ...],
  "bat_utilization": ["Floater", "Anchor", "PlaysSpinWell", "PlaysPaceWell", ...],
  "bowl_utilization": ["CanBowl4Overs", "2OverPartTimer", ...],
  "international_leagues": [["league", "team", year]],
  "ipl_experience": [[year, "team"]],
  "scouting": ["team1", "team2"],
  "smat_performance": [...],
  "quality": "A|B",
  "quality_tier": "A|B",
  "conditions_adaptability": 0.0-1.0,
  "advanced_metrics": {{
    "powerplay": {{"efscore": 100.0, "winp": 0.5, "raa": 0.0}},
    "middle_overs": {{"efscore": 100.0, "winp": 0.5, "raa": 0.0}},
    "death": {{"efscore": 100.0, "winp": 0.5, "raa": 0.0}}
  }}
}}

IMPORTANT: 
- Use the hashtag format (#TagName) for detailed_batting_tags and detailed_bowling_tags as shown in Step a) examples
- Ensure speciality classification follows Step b) criteria exactly
- Quality tier must follow Step c) criteria strictly
- Estimate advanced_metrics based on player's role, tier, and IPL experience (see Step d) above)
- For batters: Higher metrics in their primary phase (opener→PP, finisher→death)
- For bowlers: Higher metrics in their speciality phase (PP bowler→PP, death bowler→death)
"""
        return prompt
    
    def parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured data."""
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        # Fallback: try to parse as JSON directly
        try:
            return json.loads(response)
        except:
            return {}
    
    def tag_player(self, player: Player, stats_data: Optional[Dict[str, Any]] = None) -> Player:
        """Tag a player using LLM."""
        prompt = self.create_tagging_prompt(player, stats_data)
        
        try:
            response = self.client.generate_content(prompt)
            tags = self.parse_llm_response(response)
            
            # Apply tags to player
            if tags.get('primary_role'):
                try:
                    player.primary_role = PrimaryRole(tags['primary_role'])
                except:
                    pass
            
            if tags.get('batting_role'):
                try:
                    player.batting_role = BattingRole(tags['batting_role'])
                except:
                    pass
            
            if tags.get('bowling_role'):
                try:
                    player.bowling_role = BowlingRole(tags['bowling_role'])
                except:
                    pass
            
            if tags.get('speciality'):
                try:
                    player.speciality = Speciality(tags['speciality'])
                except:
                    pass
            
            if tags.get('quality'):
                try:
                    player.quality = Quality(tags['quality'])
                except:
                    pass
            
            player.bat_utilization = tags.get('bat_utilization', [])
            player.bowl_utilization = tags.get('bowl_utilization', [])
            player.international_leagues = [tuple(x) for x in tags.get('international_leagues', [])]
            player.ipl_experience = [tuple(x) for x in tags.get('ipl_experience', [])]
            player.scouting = tags.get('scouting', [])
            player.smat_performance = tags.get('smat_performance', [])
            
            # Store detailed hashtag-based tags from AuctionPrompt.md format
            player.metadata['detailed_batting_tags'] = tags.get('detailed_batting_tags', [])
            player.metadata['detailed_bowling_tags'] = tags.get('detailed_bowling_tags', [])
            player.metadata['nationality_classification'] = tags.get('nationality_classification', player.country)
            player.metadata['quality_tier'] = tags.get('quality_tier', tags.get('quality', 'B'))
            
            # Store conditions adaptability in metadata
            player.metadata['conditions_adaptability'] = tags.get('conditions_adaptability', 0.5)
            
            # Set advanced metrics if provided
            if 'advanced_metrics' in tags:
                from models.player import PhaseMetrics
                metrics = PhaseMetrics()
                adv_metrics = tags['advanced_metrics']
                
                if 'powerplay' in adv_metrics:
                    pp = adv_metrics['powerplay']
                    metrics.powerplay = {
                        'efscore': float(pp.get('efscore', 100.0)),
                        'winp': float(pp.get('winp', 0.5)),
                        'raa': float(pp.get('raa', 0.0))
                    }
                
                if 'middle_overs' in adv_metrics:
                    mo = adv_metrics['middle_overs']
                    metrics.middle_overs = {
                        'efscore': float(mo.get('efscore', 100.0)),
                        'winp': float(mo.get('winp', 0.5)),
                        'raa': float(mo.get('raa', 0.0))
                    }
                
                if 'death' in adv_metrics:
                    death = adv_metrics['death']
                    metrics.death = {
                        'efscore': float(death.get('efscore', 100.0)),
                        'winp': float(death.get('winp', 0.5)),
                        'raa': float(death.get('raa', 0.0))
                    }
                
                player.advanced_metrics = metrics
        
        except Exception as e:
            print(f"Error tagging player {player.name}: {e}")
        
        return player
    
    def create_batch_tagging_prompt(self, players: List[Player], stats_data_dict: Optional[Dict[str, Dict[str, Any]]] = None) -> str:
        """Create a single prompt for tagging multiple players (up to 10)."""
        if not hasattr(self, 'prompt_loader'):
            self.prompt_loader = PromptLoader()
        
        # Load system context from AuctionPrompt.md
        system_context = self.prompt_loader.get_tagging_context()
        
        # Build player data section
        players_data = []
        for i, player in enumerate(players, 1):
            player_info = f"""
Player {i}: {player.name}
- Country: {player.country}
- Batting Hand: {player.batting_hand or 'Unknown'}
- Bowling Style: {player.bowling_style or 'N/A'}
- Base Price: {player.base_price}L"""
            
            # Add advanced metrics if available
            if player.advanced_metrics:
                pp = player.advanced_metrics.powerplay or {}
                mo = player.advanced_metrics.middle_overs or {}
                death = player.advanced_metrics.death or {}
                player_info += f"""
- Advanced Metrics:
  * Powerplay: efscore={pp.get('efscore', 'N/A')}, winp={pp.get('winp', 'N/A')}, raa={pp.get('raa', 'N/A')}
  * Middle Overs: efscore={mo.get('efscore', 'N/A')}, winp={mo.get('winp', 'N/A')}, raa={mo.get('raa', 'N/A')}
  * Death: efscore={death.get('efscore', 'N/A')}, winp={death.get('winp', 'N/A')}, raa={death.get('raa', 'N/A')}"""
            
            # Add conditions performance if available
            if player.performance_by_conditions:
                player_info += f"\n- Performance by conditions: {json.dumps(player.performance_by_conditions)}"
            
            # Add additional stats if available
            if stats_data_dict and player.name in stats_data_dict:
                player_info += f"\n- Additional Stats: {json.dumps(stats_data_dict[player.name])}"
            
            players_data.append(player_info)
        
        players_section = "\n".join(players_data)
        
        prompt = f"""{system_context}

=== BATCH PLAYER ANALYSIS TASK ===

Using the instructions from AuctionPrompt.md above, analyze the following {len(players)} cricket players and assign comprehensive tags following Step a), b), and c).

{players_section}

=== ASSIGNMENT REQUIREMENTS ===

For EACH player, follow these steps:

Step a) - Assign detailed batting and bowling tags:
- Detailed batting tags (if applicable): Use hashtag format like #Opener, #Top3Anchor, #MiddleOrder, #Finisher, #PowerHitter, #SpinHitter, #PlaysPaceWell, #PlaysSpinWell, #WK, #BattingOrder456, etc.
- Detailed bowling tags (if applicable): Use hashtag format like #PPBowler, #MiddleOvers, #DeathOvers, #CanBowl4Overs, #2OverPartTimer, #RightArmFast, #LeftArmPace, #Legspin, #Offspin, #LeftArmOrthodox, #MysterySpinner, etc.
- Reference the CSK examples provided in the instructions for tag format

Step b) - Classify into exactly one speciality category:
- Classify as: Batter, BatAR (bat-dominant AR, ≤2 overs), BowlAR (bowl-dominant AR, 2-4 overs), SpinBowler, or FastBowler
- Also specify if Indian or Foreigner (10 specialities total: 5 types × 2 nationalities)
- Follow the specific criteria for each category from Step b)

Step c) - Assign Quality Tier:
- Tier A: First-choice for country/franchise OR clearly strong in a defined T20 role (proven IPL record or strong recent form) OR salary >=3Cr OR featured in teams scorecard 8/10 times in last year
- Tier B: Backup option, undefined role, limited sample, or average record (anything other than Tier A)

ADDITIONAL REQUIREMENT - Estimate Advanced Metrics (Phase-wise):
For each player, based on the analysis from AuctionPrompt.md above, estimate phase-wise metrics:
- **efscore** (Expected Runs vs Actual): Score 0-200, where 100 = average performance
  * Powerplay: For openers/PP specialists, typically 100-150. For others, 80-120
  * Middle Overs: For middle-order/anchors, typically 100-140. For others, 80-120
  * Death: For finishers/death specialists, typically 100-160. For others, 80-120
- **winp** (Win Probability Added): Score 0.0-1.0, where 0.5 = neutral
  * Powerplay: 0.4-0.6 for specialists, 0.45-0.55 for others
  * Middle Overs: 0.45-0.65 for key players, 0.45-0.55 for others
  * Death: 0.5-0.7 for finishers, 0.45-0.55 for others
- **raa** (Runs Above Average): Score -20 to +30 typically
  * Powerplay: +5 to +15 for good openers, -5 to +5 for others
  * Middle Overs: +5 to +20 for strong middle-order, -5 to +5 for others
  * Death: +10 to +25 for finishers, -5 to +5 for others

Estimate based on:
- Tier A players: Higher metrics (efscore 110-150, winp 0.55-0.7, raa +10 to +25)
- Tier B players: Average to below average (efscore 80-110, winp 0.45-0.55, raa -5 to +10)
- Role-specific: Openers excel in PP, finishers in death, all-rounders balanced
- IPL experience: More experience = more reliable metrics

Respond in JSON format with an array of player tags:
{{
  "players": [
    {{
      "player_name": "Player Name 1",
      "primary_role": "Batter|BatAR|BowlAR|SpinBowler|FastBowler",
      "nationality_classification": "Indian|Foreigner",
      "batting_role": "Opener|MiddleOrder|Finisher",
      "bowling_role": "Pacer|WristSpinner|FingerSpinner|LeftArmSpinner|LegSpin|OffSpin|MysterySpinner|N/A",
      "speciality": "WKBat|PPBowler|MOBowler|DeathBowler|N/A",
      "detailed_batting_tags": ["#Opener", "#PowerHitter", ...],
      "detailed_bowling_tags": ["#PPBowler", "#CanBowl4Overs", ...],
      "bat_utilization": ["Floater", "Anchor", "PlaysSpinWell", "PlaysPaceWell", ...],
      "bowl_utilization": ["CanBowl4Overs", "2OverPartTimer", ...],
      "international_leagues": [["league", "team", year]],
      "ipl_experience": [[year, "team"]],
      "scouting": ["team1", "team2"],
      "smat_performance": [...],
      "quality": "A|B",
      "quality_tier": "A|B",
      "conditions_adaptability": 0.0-1.0,
      "advanced_metrics": {{
        "powerplay": {{
          "efscore": 100.0,
          "winp": 0.5,
          "raa": 0.0
        }},
        "middle_overs": {{
          "efscore": 100.0,
          "winp": 0.5,
          "raa": 0.0
        }},
        "death": {{
          "efscore": 100.0,
          "winp": 0.5,
          "raa": 0.0
        }}
      }}
    }},
    {{
      "player_name": "Player Name 2",
      ...
      "advanced_metrics": {{
        "powerplay": {{"efscore": 100.0, "winp": 0.5, "raa": 0.0}},
        "middle_overs": {{"efscore": 100.0, "winp": 0.5, "raa": 0.0}},
        "death": {{"efscore": 100.0, "winp": 0.5, "raa": 0.0}}
      }}
    }}
  ]
}}

IMPORTANT: 
- Return tags for ALL {len(players)} players in the response
- Use the hashtag format (#TagName) for detailed_batting_tags and detailed_bowling_tags
- Ensure speciality classification follows Step b) criteria exactly
- Quality tier must follow Step c) criteria strictly
"""
        return prompt
    
    def parse_batch_llm_response(self, response: str) -> Dict[str, Dict[str, Any]]:
        """Parse LLM batch response into dictionary mapping player names to tags."""
        import re
        # Try to extract JSON from response
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group(0))
                # Convert array to dictionary
                result = {}
                if 'players' in data:
                    for player_data in data['players']:
                        player_name = player_data.get('player_name', '')
                        if player_name:
                            result[player_name] = player_data
                return result
            except:
                pass
        
        # Fallback: try to parse as JSON directly
        try:
            data = json.loads(response)
            result = {}
            if 'players' in data:
                for player_data in data['players']:
                    player_name = player_data.get('player_name', '')
                    if player_name:
                        result[player_name] = player_data
            return result
        except:
            return {}
    
    def tag_players_batch(self, players: List[Player], stats_data_dict: Optional[Dict[str, Dict[str, Any]]] = None) -> List[Player]:
        """Tag multiple players in a single LLM call (batch of up to 10)."""
        if len(players) > 10:
            raise ValueError("Batch size cannot exceed 10 players")
        
        # Create batch prompt
        prompt = self.create_batch_tagging_prompt(players, stats_data_dict)
        
        try:
            # Single LLM call for all players
            response = self.client.generate_content(prompt)
            tags_dict = self.parse_batch_llm_response(response)
            
            # Apply tags to each player
            tagged_players = []
            for player in players:
                player_tags = tags_dict.get(player.name, {})
                
                # Apply tags to player (same logic as tag_player)
                if player_tags.get('primary_role'):
                    try:
                        player.primary_role = PrimaryRole(player_tags['primary_role'])
                    except:
                        pass
                
                if player_tags.get('batting_role'):
                    try:
                        player.batting_role = BattingRole(player_tags['batting_role'])
                    except:
                        pass
                
                if player_tags.get('bowling_role'):
                    try:
                        player.bowling_role = BowlingRole(player_tags['bowling_role'])
                    except:
                        pass
                
                if player_tags.get('speciality'):
                    try:
                        player.speciality = Speciality(player_tags['speciality'])
                    except:
                        pass
                
                if player_tags.get('quality'):
                    try:
                        player.quality = Quality(player_tags['quality'])
                    except:
                        pass
                
                player.bat_utilization = player_tags.get('bat_utilization', [])
                player.bowl_utilization = player_tags.get('bowl_utilization', [])
                player.international_leagues = [tuple(x) for x in player_tags.get('international_leagues', [])]
                player.ipl_experience = [tuple(x) for x in player_tags.get('ipl_experience', [])]
                player.scouting = player_tags.get('scouting', [])
                player.smat_performance = player_tags.get('smat_performance', [])
                
                # Store detailed hashtag-based tags
                player.metadata['detailed_batting_tags'] = player_tags.get('detailed_batting_tags', [])
                player.metadata['detailed_bowling_tags'] = player_tags.get('detailed_bowling_tags', [])
                player.metadata['nationality_classification'] = player_tags.get('nationality_classification', player.country)
                player.metadata['quality_tier'] = player_tags.get('quality_tier', player_tags.get('quality', 'B'))
                player.metadata['conditions_adaptability'] = player_tags.get('conditions_adaptability', 0.5)
                
                # Set advanced metrics if provided
                if 'advanced_metrics' in player_tags:
                    from models.player import PhaseMetrics
                    metrics = PhaseMetrics()
                    adv_metrics = player_tags['advanced_metrics']
                    
                    if 'powerplay' in adv_metrics:
                        pp = adv_metrics['powerplay']
                        metrics.powerplay = {
                            'efscore': float(pp.get('efscore', 100.0)),
                            'winp': float(pp.get('winp', 0.5)),
                            'raa': float(pp.get('raa', 0.0))
                        }
                    
                    if 'middle_overs' in adv_metrics:
                        mo = adv_metrics['middle_overs']
                        metrics.middle_overs = {
                            'efscore': float(mo.get('efscore', 100.0)),
                            'winp': float(mo.get('winp', 0.5)),
                            'raa': float(mo.get('raa', 0.0))
                        }
                    
                    if 'death' in adv_metrics:
                        death = adv_metrics['death']
                        metrics.death = {
                            'efscore': float(death.get('efscore', 100.0)),
                            'winp': float(death.get('winp', 0.5)),
                            'raa': float(death.get('raa', 0.0))
                        }
                    
                    player.advanced_metrics = metrics
                
                tagged_players.append(player)
            
            return tagged_players
            
        except Exception as e:
            print(f"Error in batch tagging: {e}")
            # Fallback to individual tagging if batch fails
            tagged = []
            for player in players:
                try:
                    tagged_player = self.tag_player(player, stats_data_dict.get(player.name) if stats_data_dict else None)
                    tagged.append(tagged_player)
                except:
                    tagged.append(player)  # Return untagged player if tagging fails
            return tagged

