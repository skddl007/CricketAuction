"""File handler for batch updates."""

import csv
import json
from typing import List, Dict, Any
from pathlib import Path
from core.state_manager import StateManager
from utils import parse_price_string, normalize_team_name


class FileHandler:
    """Handle file-based auction updates."""
    
    def __init__(self, state_manager: StateManager):
        """Initialize file handler."""
        self.state_manager = state_manager
    
    def load_from_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Load auction updates from CSV file."""
        updates = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                updates.append({
                    'player_name': row.get('player_name', '').strip(),
                    'team': normalize_team_name(row.get('team', '').strip()),
                    'price': parse_price_string(row.get('price', '')),
                    'timestamp': row.get('timestamp', '')
                })
        
        return updates
    
    def load_from_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load auction updates from JSON file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and 'updates' in data:
            return data['updates']
        else:
            return []
    
    def apply_updates(self, updates: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply batch updates to state."""
        results = {
            'success': [],
            'errors': []
        }
        
        for update in updates:
            player_name = update.get('player_name')
            team_name = update.get('team')
            price = update.get('price')
            
            if not all([player_name, team_name, price]):
                results['errors'].append({
                    'update': update,
                    'error': 'Missing required fields'
                })
                continue
            
            try:
                self.state_manager.sell_player(player_name, team_name, price, update.get('timestamp'))
                results['success'].append(update)
            except Exception as e:
                results['errors'].append({
                    'update': update,
                    'error': str(e)
                })
        
        return results
    
    def export_state(self, file_path: str):
        """Export current state to file."""
        self.state_manager.export_state(file_path)
    
    def import_state(self, file_path: str):
        """Import state from file."""
        self.state_manager.import_state(file_path)

