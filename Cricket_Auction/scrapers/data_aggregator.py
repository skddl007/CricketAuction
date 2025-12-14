"""Data aggregator to combine all data sources."""

from typing import Dict, List, Any, Optional
from models.player import Player
from pathlib import Path
import json


class DataAggregator:
    """Aggregate data from multiple sources."""
    
    def __init__(self, cache_dir: str = "cache/aggregated"):
        """Initialize aggregator."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def aggregate_player_data(
        self,
        player: Player,
        scraped_stats: Optional[Dict[str, Any]] = None,
        cricsheet_data: Optional[Dict[str, Any]] = None,
        u19_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Aggregate all data sources for a player."""
        aggregated = {
            'name': player.name,
            'base_data': {
                'base_price': player.base_price,
                'country': player.country,
                'batting_hand': player.batting_hand,
                'bowling_style': player.bowling_style
            },
            'scraped_stats': scraped_stats or {},
            'cricsheet_data': cricsheet_data or {},
            'u19_data': u19_data or {},
            'advanced_metrics': player.advanced_metrics.powerplay if player.advanced_metrics else None,
            'conditions_performance': player.performance_by_conditions
        }
        
        return aggregated
    
    def combine_all_sources(self, players: List[Player]) -> Dict[str, Dict[str, Any]]:
        """Combine all data sources for all players."""
        aggregated_data = {}
        for player in players:
            aggregated_data[player.name] = self.aggregate_player_data(player)
        return aggregated_data

