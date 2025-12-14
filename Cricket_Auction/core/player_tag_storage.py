"""CSV storage for tagged player data."""

import csv
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from models.player import Player, PrimaryRole, BattingRole, BowlingRole, Speciality, Quality, PhaseMetrics


class PlayerTagStorage:
    """Store and load tagged player data from CSV."""
    
    def __init__(self, csv_path: str = "Data/TaggedPlayers.csv"):
        """Initialize tag storage."""
        self.csv_path = Path(csv_path)
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    def player_to_csv_row(self, player: Player) -> Dict[str, Any]:
        """Convert player to CSV row format."""
        # Convert lists to JSON strings for CSV storage
        bat_tags = player.metadata.get('detailed_batting_tags', [])
        bowl_tags = player.metadata.get('detailed_bowling_tags', [])
        
        row = {
            'name': player.name,
            'base_price': player.base_price,
            'country': player.country,
            'batting_hand': player.batting_hand or '',
            'bowling_style': player.bowling_style or '',
            'primary_role': player.primary_role.value if player.primary_role else '',
            'batting_role': player.batting_role.value if player.batting_role else '',
            'bowling_role': player.bowling_role.value if player.bowling_role else '',
            'speciality': player.speciality.value if player.speciality else '',
            'quality': player.quality.value if player.quality else '',
            'nationality_classification': player.metadata.get('nationality_classification', player.country),
            'quality_tier': player.metadata.get('quality_tier', ''),
            'detailed_batting_tags': json.dumps(bat_tags, ensure_ascii=False),
            'detailed_bowling_tags': json.dumps(bowl_tags, ensure_ascii=False),
            'bat_utilization': json.dumps(player.bat_utilization, ensure_ascii=False),
            'bowl_utilization': json.dumps(player.bowl_utilization, ensure_ascii=False),
            'international_leagues': json.dumps([list(x) for x in player.international_leagues], ensure_ascii=False),
            'ipl_experience': json.dumps([list(x) for x in player.ipl_experience], ensure_ascii=False),
            'scouting': json.dumps(player.scouting, ensure_ascii=False),
            'smat_performance': json.dumps(player.smat_performance, ensure_ascii=False),
            'conditions_adaptability': str(player.metadata.get('conditions_adaptability', 0.5)),
        }
        
        # Advanced metrics
        if player.advanced_metrics:
            row['pp_efscore'] = str(player.advanced_metrics.powerplay.get('efscore', '')) if player.advanced_metrics.powerplay else ''
            row['pp_winp'] = str(player.advanced_metrics.powerplay.get('winp', '')) if player.advanced_metrics.powerplay else ''
            row['pp_raa'] = str(player.advanced_metrics.powerplay.get('raa', '')) if player.advanced_metrics.powerplay else ''
            row['mo_efscore'] = str(player.advanced_metrics.middle_overs.get('efscore', '')) if player.advanced_metrics.middle_overs else ''
            row['mo_winp'] = str(player.advanced_metrics.middle_overs.get('winp', '')) if player.advanced_metrics.middle_overs else ''
            row['mo_raa'] = str(player.advanced_metrics.middle_overs.get('raa', '')) if player.advanced_metrics.middle_overs else ''
            row['death_efscore'] = str(player.advanced_metrics.death.get('efscore', '')) if player.advanced_metrics.death else ''
            row['death_winp'] = str(player.advanced_metrics.death.get('winp', '')) if player.advanced_metrics.death else ''
            row['death_raa'] = str(player.advanced_metrics.death.get('raa', '')) if player.advanced_metrics.death else ''
        else:
            for key in ['pp_efscore', 'pp_winp', 'pp_raa', 'mo_efscore', 'mo_winp', 'mo_raa', 
                       'death_efscore', 'death_winp', 'death_raa']:
                row[key] = ''
        
        return row
    
    def csv_row_to_player(self, row: Dict[str, str]) -> Player:
        """Convert CSV row to Player object."""
        # Create base player
        player = Player(
            name=row['name'],
            base_price=int(row.get('base_price', 0)),
            country=row.get('country', 'Indian'),
            batting_hand=row.get('batting_hand') or None,
            bowling_style=row.get('bowling_style') or None
        )
        
        # Set enums
        if row.get('primary_role'):
            try:
                player.primary_role = PrimaryRole(row['primary_role'])
            except:
                pass
        
        if row.get('batting_role'):
            try:
                player.batting_role = BattingRole(row['batting_role'])
            except:
                pass
        
        if row.get('bowling_role'):
            try:
                player.bowling_role = BowlingRole(row['bowling_role'])
            except:
                pass
        
        if row.get('speciality'):
            try:
                player.speciality = Speciality(row['speciality'])
            except:
                pass
        
        if row.get('quality'):
            try:
                player.quality = Quality(row['quality'])
            except:
                pass
        
        # Parse JSON fields
        try:
            player.bat_utilization = json.loads(row.get('bat_utilization', '[]'))
        except:
            player.bat_utilization = []
        
        try:
            player.bowl_utilization = json.loads(row.get('bowl_utilization', '[]'))
        except:
            player.bowl_utilization = []
        
        try:
            leagues = json.loads(row.get('international_leagues', '[]'))
            player.international_leagues = [tuple(x) for x in leagues]
        except:
            player.international_leagues = []
        
        try:
            ipl_exp = json.loads(row.get('ipl_experience', '[]'))
            player.ipl_experience = [tuple(x) for x in ipl_exp]
        except:
            player.ipl_experience = []
        
        try:
            player.scouting = json.loads(row.get('scouting', '[]'))
        except:
            player.scouting = []
        
        try:
            player.smat_performance = json.loads(row.get('smat_performance', '[]'))
        except:
            player.smat_performance = []
        
        # Metadata
        try:
            player.metadata['detailed_batting_tags'] = json.loads(row.get('detailed_batting_tags', '[]'))
        except:
            player.metadata['detailed_batting_tags'] = []
        
        try:
            player.metadata['detailed_bowling_tags'] = json.loads(row.get('detailed_bowling_tags', '[]'))
        except:
            player.metadata['detailed_bowling_tags'] = []
        
        player.metadata['nationality_classification'] = row.get('nationality_classification', player.country)
        player.metadata['quality_tier'] = row.get('quality_tier', '')
        
        try:
            player.metadata['conditions_adaptability'] = float(row.get('conditions_adaptability', '0.5'))
        except:
            player.metadata['conditions_adaptability'] = 0.5
        
        # Advanced metrics
        metrics = PhaseMetrics()
        try:
            if row.get('pp_efscore'):
                metrics.powerplay = {
                    'efscore': float(row['pp_efscore']) if row['pp_efscore'] else None,
                    'winp': float(row['pp_winp']) if row.get('pp_winp') else None,
                    'raa': float(row['pp_raa']) if row.get('pp_raa') else None
                }
        except:
            pass
        
        try:
            if row.get('mo_efscore'):
                metrics.middle_overs = {
                    'efscore': float(row['mo_efscore']) if row['mo_efscore'] else None,
                    'winp': float(row['mo_winp']) if row.get('mo_winp') else None,
                    'raa': float(row['mo_raa']) if row.get('mo_raa') else None
                }
        except:
            pass
        
        try:
            if row.get('death_efscore'):
                metrics.death = {
                    'efscore': float(row['death_efscore']) if row['death_efscore'] else None,
                    'winp': float(row['death_winp']) if row.get('death_winp') else None,
                    'raa': float(row['death_raa']) if row.get('death_raa') else None
                }
        except:
            pass
        
        if metrics.powerplay or metrics.middle_overs or metrics.death:
            player.advanced_metrics = metrics
        
        return player
    
    def get_csv_headers(self) -> List[str]:
        """Get CSV column headers."""
        return [
            'name', 'base_price', 'country', 'batting_hand', 'bowling_style',
            'primary_role', 'batting_role', 'bowling_role', 'speciality', 'quality',
            'nationality_classification', 'quality_tier',
            'detailed_batting_tags', 'detailed_bowling_tags',
            'bat_utilization', 'bowl_utilization',
            'international_leagues', 'ipl_experience', 'scouting', 'smat_performance',
            'conditions_adaptability',
            'pp_efscore', 'pp_winp', 'pp_raa',
            'mo_efscore', 'mo_winp', 'mo_raa',
            'death_efscore', 'death_winp', 'death_raa'
        ]
    
    def save_players(self, players: List[Player], append: bool = False):
        """Save players to CSV."""
        file_exists = self.csv_path.exists()
        mode = 'a' if append and file_exists else 'w'
        
        with open(self.csv_path, mode, newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.get_csv_headers())
            
            if not (append and file_exists):
                writer.writeheader()
            
            for player in players:
                row = self.player_to_csv_row(player)
                writer.writerow(row)
    
    def load_players(self) -> Dict[str, Player]:
        """Load all tagged players from CSV."""
        if not self.csv_path.exists():
            return {}
        
        players = {}
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    player = self.csv_row_to_player(row)
                    players[player.name] = player
                except Exception as e:
                    print(f"Warning: Could not load player {row.get('name', 'Unknown')}: {e}")
                    continue
        
        return players
    
    def get_tagged_player_names(self) -> List[str]:
        """Get list of already tagged player names."""
        if not self.csv_path.exists():
            return []
        
        names = []
        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('name'):
                    names.append(row['name'])
        
        return names
    
    def update_player(self, player: Player):
        """Update a single player in CSV (removes old entry and adds new)."""
        # Load all players
        all_players = self.load_players()
        
        # Update the specific player
        all_players[player.name] = player
        
        # Save all players
        self.save_players(list(all_players.values()), append=False)
    
    def player_is_tagged(self, player_name: str) -> bool:
        """Check if a player is already tagged."""
        return player_name in self.get_tagged_player_names()

