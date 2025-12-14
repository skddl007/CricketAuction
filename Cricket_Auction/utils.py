"""Utility functions."""

from typing import Optional, List
import re


def lakhs_to_crores(lakhs: int) -> float:
    """Convert lakhs to crores."""
    return lakhs / 100.0


def crores_to_lakhs(crores: float) -> int:
    """Convert crores to lakhs."""
    return int(crores * 100)


def format_price(lakhs: int, unit: str = "Cr") -> str:
    """Format price for display."""
    if unit == "Cr":
        return f"{lakhs_to_crores(lakhs):.1f} Cr"
    else:
        return f"{lakhs}L"


def match_player_name(name: str, players: List) -> Optional:
    """Match player name with variations."""
    name_lower = name.lower().strip()
    
    for player in players:
        if hasattr(player, 'name'):
            player_name = player.name.lower().strip()
            if player_name == name_lower:
                return player
            # Check for partial matches
            if name_lower in player_name or player_name in name_lower:
                return player
    
    return None


def parse_price_string(price_str: str) -> Optional[int]:
    """Parse price string like '15Cr' or '1500L' to lakhs."""
    price_str = price_str.strip().upper()
    
    # Try crores
    match = re.search(r'(\d+\.?\d*)\s*CR', price_str)
    if match:
        crores = float(match.group(1))
        return crores_to_lakhs(crores)
    
    # Try lakhs
    match = re.search(r'(\d+)\s*L', price_str)
    if match:
        return int(match.group(1))
    
    # Try just number (assume crores)
    match = re.search(r'(\d+\.?\d*)', price_str)
    if match:
        crores = float(match.group(1))
        return crores_to_lakhs(crores)
    
    return None


def validate_player_name(name: str) -> bool:
    """Validate player name format."""
    if not name or len(name) < 2:
        return False
    return True


def validate_team_name(name: str) -> bool:
    """Validate team name."""
    valid_teams = ['CSK', 'RCB', 'MI', 'KKR', 'DC', 'GT', 'LSG', 'PBKS', 'RR', 'SRH']
    return name.upper() in valid_teams


def normalize_team_name(name: str) -> str:
    """Normalize team name to standard format."""
    name = name.upper().strip()
    team_mapping = {
        'CHENNAI': 'CSK',
        'BANGALORE': 'RCB',
        'BENGALURU': 'RCB',
        'MUMBAI': 'MI',
        'KOLKATA': 'KKR',
        'DELHI': 'DC',
        'GUJARAT': 'GT',
        'LUCKNOW': 'LSG',
        'PUNJAB': 'PBKS',
        'RAJASTHAN': 'RR',
        'HYDERABAD': 'SRH',
        'SUNRISERS': 'SRH'
    }
    return team_mapping.get(name, name)


def parse_llm_json_response(response: str) -> dict:
    """Parse JSON from LLM response."""
    import json
    import re
    
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

