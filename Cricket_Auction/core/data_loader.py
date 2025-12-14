"""CSV data loader for Supply, RetainedPlayers, and PurseBalance."""

import csv
import re
from typing import List, Dict, Optional
from pathlib import Path

from models.player import Player
from models.team import Team


def parse_supply_csv(file_path: str) -> List[Player]:
    """Parse Supply.csv and return list of Player objects."""
    players = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        # Skip first line (header "Supply")
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            # Parse the row which has format like:
            # Sl.No: 1|Set.No: 1|Name: Devon Conway|BasePrice: 200L|Country: New Zealand|LHB|
            
            # Extract fields using regex
            name_match = re.search(r'Name:\s*([^|]+)', line)
            base_price_match = re.search(r'BasePrice:\s*(\d+)L', line)
            country_match = re.search(r'Country:\s*([^|]+)', line)
            batting_hand_match = re.search(r'(LHB|RHB)', line)
            bowling_style_match = re.search(r'(LEFT|RIGHT)\s+ARM\s+([^|]+)', line)
            
            if not name_match or not base_price_match or not country_match:
                continue
            
            name = name_match.group(1).strip()
            base_price = int(base_price_match.group(1))
            country = country_match.group(1).strip()
            batting_hand = batting_hand_match.group(1) if batting_hand_match else None
            
            bowling_style = None
            if bowling_style_match:
                arm = bowling_style_match.group(1)
                style = bowling_style_match.group(2).strip()
                bowling_style = f"{arm} ARM {style}"
            elif re.search(r'(LEFT|RIGHT)\s+ARM', line):
                # Fallback: just extract ARM type
                arm_match = re.search(r'(LEFT|RIGHT)\s+ARM', line)
                if arm_match:
                    bowling_style = arm_match.group(0)
            
            player = Player(
                name=name,
                base_price=base_price,
                country=country,
                batting_hand=batting_hand,
                bowling_style=bowling_style
            )
            
            players.append(player)
    
    return players


def parse_retained_players_csv(file_path: str, players: List[Player]) -> Dict[str, List[Player]]:
    """Parse RetainedPlayers.csv and return dict mapping team names to retained players."""
    team_players = {}
    player_lookup = {p.name: p for p in players}
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            player_name = row['Player'].strip()
            team_name = row['RetainedTeam'].strip()
            
            if player_name in player_lookup:
                if team_name not in team_players:
                    team_players[team_name] = []
                team_players[team_name].append(player_lookup[player_name])
            else:
                # Create new player if not in supply
                player = Player(
                    name=player_name,
                    base_price=0,  # Retained players don't have base price
                    country=row.get('Nationality', 'Indian').strip()
                )
                if team_name not in team_players:
                    team_players[team_name] = []
                team_players[team_name].append(player)
    
    return team_players


def parse_purse_balance_csv(file_path: str) -> Dict[str, Dict]:
    """Parse PurseBalance.csv and return dict with team financial data."""
    teams_data = {}
    
    # Home ground mapping
    home_grounds = {
        'CSK': ('Chepauk', 'spin-friendly'),
        'RCB': ('Chinnaswamy', 'batting-friendly'),
        'MI': ('Wankhede', 'pace-friendly'),
        'KKR': ('Eden Gardens', 'balanced'),
        'DC': ('Arun Jaitley', 'balanced'),
        'GT': ('Ahmedabad', 'pace-friendly'),
        'LSG': ('Lucknow', 'balanced'),
        'PBKS': ('Mohali', 'pace-friendly'),
        'RR': ('Jaipur', 'balanced'),
        'SRH': ('Hyderabad', 'balanced')
    }
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            team_name = row['Team'].strip()
            home_ground, ground_condition = home_grounds.get(team_name, ('Unknown', 'balanced'))
            
            teams_data[team_name] = {
                'name': team_name,
                'home_ground': home_ground,
                'ground_condition': ground_condition,
                'players_retained': int(row['PlayersRetained']),
                'foreign_players_retained': int(row['NoofForeignPlayers']),
                'retention_spends': int(row['RetentionSpends_IPL2026(Lakhs)']),
                'purse_available': int(row['PurseAvailable_IPL 2026(Lakhs)']),
                'total_slots': int(row['AvailableSlots']) + int(row['PlayersRetained']),
                'foreign_slots': int(row['AvailableForeignerSlots']) + int(row['NoofForeignPlayers'])
            }
    
    return teams_data


def load_all_data(data_dir: str | Path = "Data") -> tuple[List[Player], Dict[str, Team]]:
    """Load all CSV data and return players and teams."""
    data_path = Path(data_dir) if isinstance(data_dir, str) else data_dir
    data_path = data_path.resolve()  # Resolve to absolute path
    
    # Load supply
    supply_path = data_path / "Supply.csv"
    if not supply_path.exists():
        raise FileNotFoundError(
            f"Supply.csv not found at {supply_path}. "
            f"Please ensure the Data directory exists in the project root."
        )
    players = parse_supply_csv(str(supply_path))
    
    # Load retained players
    retained_path = data_path / "RetainedPlayers.csv"
    if not retained_path.exists():
        raise FileNotFoundError(
            f"RetainedPlayers.csv not found at {retained_path}. "
            f"Please ensure the Data directory exists in the project root."
        )
    team_retained = parse_retained_players_csv(str(retained_path), players)
    
    # Load purse balance
    purse_path = data_path / "PurseBalance.csv"
    if not purse_path.exists():
        raise FileNotFoundError(
            f"PurseBalance.csv not found at {purse_path}. "
            f"Please ensure the Data directory exists in the project root."
        )
    teams_data = parse_purse_balance_csv(str(purse_path))
    
    # Create Team objects
    teams = {}
    for team_name, team_info in teams_data.items():
        retained = team_retained.get(team_name, [])
        team = Team(
            name=team_info['name'],
            home_ground=team_info['home_ground'],
            ground_condition=team_info['ground_condition'],
            purse_available=team_info['purse_available'],
            total_slots=team_info['total_slots'],
            foreign_slots=team_info['foreign_slots'],
            players_retained=team_info['players_retained'],
            foreign_players_retained=team_info['foreign_players_retained'],
            retention_spends=team_info['retention_spends'],
            retained_players=retained
        )
        teams[team_name] = team
    
    return players, teams

