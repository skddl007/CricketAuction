"""Cricsheet.org data fetcher for ball-by-ball match data."""

import requests
import json
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any
import time


class CricsheetFetcher:
    """Fetches and parses match data from cricsheet.org."""
    
    BASE_URL = "https://cricsheet.org"
    CACHE_DIR = Path("cache/cricsheet")
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize fetcher."""
        if cache_dir:
            self.CACHE_DIR = Path(cache_dir)
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    def download_match_list(self, competition: str, year: Optional[int] = None) -> List[str]:
        """Download list of match IDs for a competition."""
        # Cricsheet.org provides match lists in YAML format
        if year:
            url = f"{self.BASE_URL}/matches/{competition}_{year}.yaml"
        else:
            url = f"{self.BASE_URL}/matches/{competition}.yaml"
        
        cache_file = self.CACHE_DIR / f"{competition}_{year or 'all'}_list.yaml"
        
        # Check cache
        if cache_file.exists():
            with open(cache_file, 'r', encoding='utf-8') as f:
                try:
                    data = yaml.safe_load(f)
                    return [match.get('id', '') for match in data if match.get('id')]
                except:
                    pass
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            
            data = yaml.safe_load(response.text)
            return [match.get('id', '') for match in data if match.get('id')]
        except Exception as e:
            print(f"Error downloading match list: {e}")
            return []
    
    def download_match(self, match_id: str, competition: str) -> Optional[Dict[str, Any]]:
        """Download a single match by ID."""
        cache_file = self.CACHE_DIR / f"{competition}_{match_id}.yaml"
        
        # Check cache
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f)
            except Exception as e:
                print(f"Error reading cached match {match_id}: {e}")
        
        # Download match
        url = f"{self.BASE_URL}/matches/{match_id}.yaml"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            match_data = yaml.safe_load(response.text)
            
            # Save to cache
            with open(cache_file, 'w', encoding='utf-8') as f:
                yaml.dump(match_data, f, default_flow_style=False, allow_unicode=True)
            
            return match_data
        except Exception as e:
            print(f"Error downloading match {match_id}: {e}")
            return None
    
    def download_competition_matches(self, competition: str, year: Optional[int] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Download all matches for a competition."""
        match_ids = self.download_match_list(competition, year)
        
        if limit:
            match_ids = match_ids[:limit]
        
        matches = []
        for i, match_id in enumerate(match_ids):
            print(f"Downloading match {i+1}/{len(match_ids)}: {match_id}")
            match_data = self.download_match(match_id, competition)
            if match_data:
                matches.append(match_data)
            
            # Rate limiting
            time.sleep(0.5)
        
        return matches
    
    def parse_match_for_player(self, match_data: Dict[str, Any], player_name: str) -> List[Dict[str, Any]]:
        """Extract player performance data from match."""
        performances = []
        
        if 'innings' not in match_data:
            return performances
        
        for innings in match_data['innings']:
            team = innings.get('team', '')
            deliveries = innings.get('deliveries', [])
            
            # Track wickets fallen
            wickets_fallen = 0
            
            for over_num, over_data in deliveries.items():
                for ball_num, ball_data in over_data.items():
                    # Check if player batted
                    if 'batter' in ball_data and player_name.lower() in ball_data['batter'].lower():
                        runs = ball_data.get('runs', {}).get('batter', 0)
                        over = int(float(over_num))
                        
                        # Determine phase
                        if over <= 6:
                            phase = "powerplay"
                        elif over <= 15:
                            phase = "middle_overs"
                        else:
                            phase = "death"
                        
                        performances.append({
                            'over': over,
                            'ball': ball_num,
                            'runs': runs,
                            'phase': phase,
                            'wickets_fallen': wickets_fallen,
                            'team': team
                        })
                    
                    # Check if player bowled
                    if 'bowler' in ball_data and player_name.lower() in ball_data['bowler'].lower():
                        runs = ball_data.get('runs', {}).get('total', 0)
                        wicket = 'wicket' in ball_data
                        over = int(float(over_num))
                        
                        if over <= 6:
                            phase = "powerplay"
                        elif over <= 15:
                            phase = "middle_overs"
                        else:
                            phase = "death"
                        
                        performances.append({
                            'over': over,
                            'ball': ball_num,
                            'runs_conceded': runs,
                            'wicket': wicket,
                            'phase': phase,
                            'team': team
                        })
                    
                    # Track wickets
                    if 'wicket' in ball_data:
                        wickets_fallen += 1
        
        return performances
    
    def get_player_matches(self, player_name: str, competitions: List[str], years: Optional[List[int]] = None) -> List[Dict[str, Any]]:
        """Get all matches for a player across competitions."""
        all_matches = []
        
        for competition in competitions:
            if years:
                for year in years:
                    matches = self.download_competition_matches(competition, year)
                    for match in matches:
                        performances = self.parse_match_for_player(match, player_name)
                        if performances:
                            all_matches.append({
                                'match_id': match.get('meta', {}).get('match_id', ''),
                                'competition': competition,
                                'year': year,
                                'performances': performances,
                                'match_data': match
                            })
            else:
                matches = self.download_competition_matches(competition)
                for match in matches:
                    performances = self.parse_match_for_player(match, player_name)
                    if performances:
                        all_matches.append({
                            'match_id': match.get('meta', {}).get('match_id', ''),
                            'competition': competition,
                            'performances': performances,
                            'match_data': match
                        })
        
        return all_matches

