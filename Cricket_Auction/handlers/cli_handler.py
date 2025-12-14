"""CLI handler for interactive command-line interface."""

from typing import Optional, Dict, Any, List
from core.state_manager import StateManager
from core.recommender import Recommender
from core.player_grouper import PlayerGrouper
from output.matrix_generator import MatrixGenerator
from core.player_tag_storage import PlayerTagStorage
from llm.player_tagger import PlayerTagger
from utils import parse_price_string, normalize_team_name
from models.player import Player


class CLIHandler:
    """Handle CLI commands."""
    
    def __init__(
        self,
        state_manager: StateManager,
        recommender: Optional[Recommender],
        player_grouper: Optional[PlayerGrouper],
        matrix_generator: MatrixGenerator,
        player_tagger: Optional[PlayerTagger] = None,
        tag_storage: Optional[PlayerTagStorage] = None
    ):
        """Initialize CLI handler."""
        self.state_manager = state_manager
        self.recommender = recommender
        self.player_grouper = player_grouper
        self.matrix_generator = matrix_generator
        self.player_tagger = player_tagger
        self.tag_storage = tag_storage or PlayerTagStorage()
        self.current_mode = "team_selection"
        self.selected_team = None
    
    def handle_command(self, command: str) -> str:
        """Handle a CLI command."""
        parts = command.strip().split()
        if not parts:
            return "Invalid command"
        
        cmd = parts[0].lower()
        
        if cmd == "mode":
            return self.handle_mode(parts[1] if len(parts) > 1 else None)
        elif cmd == "select_team":
            return self.handle_select_team(parts[1] if len(parts) > 1 else None)
        elif cmd == "suggest":
            return self.handle_suggest()
        elif cmd == "sell":
            return self.handle_sell(parts[1:] if len(parts) > 1 else [])
        elif cmd == "show":
            return self.handle_show(parts[1] if len(parts) > 1 else None)
        elif cmd == "state":
            return self.handle_state()
        elif cmd == "tag":
            return self.handle_tag(parts[1:] if len(parts) > 1 else [])
        elif cmd == "tag_batch":
            return self.handle_tag_batch(parts[1:] if len(parts) > 1 else [])
        elif cmd == "tag_status":
            return self.handle_tag_status()
        elif cmd == "help":
            return self.handle_help()
        else:
            return f"Unknown command: {cmd}. Type 'help' for available commands."
    
    def handle_mode(self, mode: Optional[str]) -> str:
        """Switch between modes."""
        if mode in ["team_selection", "live_bid"]:
            self.current_mode = mode
            return f"Switched to {mode} mode"
        return "Invalid mode. Use 'team_selection' or 'live_bid'"
    
    def handle_select_team(self, team_name: Optional[str]) -> str:
        """Select team for team selection mode."""
        if not team_name:
            return "Please specify team name"
        
        team_name = normalize_team_name(team_name)
        team = self.state_manager.get_team(team_name)
        if not team:
            return f"Team {team_name} not found"
        
        self.selected_team = team_name
        return f"Selected team: {team_name}"
    
    def handle_suggest(self) -> str:
        """Get grouped recommendations."""
        if not self.selected_team:
            return "Please select a team first using 'select_team <team>'"
        
        team = self.state_manager.get_team(self.selected_team)
        if not team:
            return f"Team {self.selected_team} not found"
        
        available_players = self.state_manager.get_available_players()
        groups = self.player_grouper.get_grouped_recommendations(team, available_players)
        
        return self.player_grouper.format_grouped_recommendations(team, groups)
    
    def handle_sell(self, args: list) -> str:
        """Handle player sale."""
        if len(args) < 3:
            return "Usage: sell <player_name> <team> <price>"
        
        player_name = args[0]
        team_name = normalize_team_name(args[1])
        price_str = args[2]
        
        price = parse_price_string(price_str)
        if not price:
            return f"Invalid price: {price_str}"
        
        try:
            self.state_manager.sell_player(player_name, team_name, price)
            return f"✓ {player_name} sold to {team_name} for {price_str}"
        except Exception as e:
            return f"Error: {str(e)}"
    
    def handle_show(self, team_name: Optional[str]) -> str:
        """Show team matrix."""
        if team_name:
            team_name = normalize_team_name(team_name)
            team = self.state_manager.get_team(team_name)
            if not team:
                return f"Team {team_name} not found"
            return self.matrix_generator.generate_team_matrix(team)
        else:
            return self.matrix_generator.generate_all_matrices()
    
    def handle_state(self) -> str:
        """Show current auction state."""
        supply_count = self.state_manager.get_supply_count()
        sold_count = len(self.state_manager.get_sold_players())
        teams = self.state_manager.get_all_teams()
        
        lines = [
            f"=== Auction State ===",
            f"Available Players: {supply_count}",
            f"Sold Players: {sold_count}",
            f"Teams: {len(teams)}",
            ""
        ]
        
        for team_name, team in teams.items():
            lines.append(f"{team_name}: {team.total_players} players, {team.purse_available / 100:.1f}Cr purse")
        
        return "\n".join(lines)
    
    def handle_tag(self, args: list) -> str:
        """Tag a single player or multiple players by name."""
        if not self.player_tagger:
            return "Error: Player tagger not available. GEMINI_API_KEY not set."
        
        if not args:
            return "Usage: tag <player_name1> [player_name2] ... [player_name10]\n" \
                   "       Tag 1-10 players at a time"
        
        if len(args) > 10:
            return "Error: Maximum 10 players can be tagged at once. Please tag in batches."
        
        available_players = self.state_manager.get_available_players()
        players_to_tag = []
        not_found = []
        already_tagged = []
        
        for player_name in args:
            # Find player
            player = None
            for p in available_players:
                if p.name.lower() == player_name.lower() or player_name.lower() in p.name.lower():
                    player = p
                    break
            
            if not player:
                not_found.append(player_name)
                continue
            
            # Check if already tagged
            if self.tag_storage.player_is_tagged(player.name):
                already_tagged.append(player.name)
                continue
            
            players_to_tag.append(player)
        
        if not_found:
            return f"Error: Players not found: {', '.join(not_found)}"
        
        if already_tagged:
            return f"Info: These players are already tagged: {', '.join(already_tagged)}\n" \
                   f"Use 'tag_batch' to re-tag them if needed."
        
        if not players_to_tag:
            return "No players to tag. All specified players are already tagged."
        
        # Tag players
        tagged_players = []
        results = []
        
        for player in players_to_tag:
            try:
                results.append(f"Tagging {player.name}...")
                tagged_player = self.player_tagger.tag_player(player)
                tagged_players.append(tagged_player)
                results.append(f"✓ {player.name} tagged successfully")
            except Exception as e:
                results.append(f"✗ Error tagging {player.name}: {str(e)}")
        
        # Save to CSV
        if tagged_players:
            try:
                self.tag_storage.save_players(tagged_players, append=True)
                results.append(f"\n✓ Saved {len(tagged_players)} tagged players to CSV")
            except Exception as e:
                results.append(f"\n✗ Error saving to CSV: {str(e)}")
        
        return "\n".join(results)
    
    def handle_tag_batch(self, args: list) -> str:
        """Tag next N untagged players (default: 10)."""
        if not self.player_tagger:
            return "Error: Player tagger not available. GEMINI_API_KEY not set."
        
        # Get batch size
        batch_size = 10
        if args and args[0].isdigit():
            batch_size = int(args[0])
            if batch_size < 1 or batch_size > 10:
                return "Error: Batch size must be between 1 and 10"
        
        # Get untagged players
        available_players = self.state_manager.get_available_players()
        tagged_names = set(self.tag_storage.get_tagged_player_names())
        untagged_players = [p for p in available_players if p.name not in tagged_names]
        
        if not untagged_players:
            return "All players are already tagged!"
        
        # Take batch
        batch = untagged_players[:batch_size]
        
        results = [f"Tagging {len(batch)} players...", ""]
        tagged_players = []
        
        for i, player in enumerate(batch, 1):
            try:
                results.append(f"[{i}/{len(batch)}] Tagging {player.name}...")
                tagged_player = self.player_tagger.tag_player(player)
                tagged_players.append(tagged_player)
                results.append(f"  ✓ {player.name} - {tagged_player.primary_role.value if tagged_player.primary_role else 'N/A'}")
            except Exception as e:
                results.append(f"  ✗ Error: {str(e)}")
        
        # Save to CSV
        if tagged_players:
            try:
                self.tag_storage.save_players(tagged_players, append=True)
                results.append(f"\n✓ Saved {len(tagged_players)} players to CSV")
                results.append(f"Progress: {len(tagged_names) + len(tagged_players)}/{len(available_players)} players tagged")
            except Exception as e:
                results.append(f"\n✗ Error saving to CSV: {str(e)}")
        
        return "\n".join(results)
    
    def handle_tag_status(self) -> str:
        """Show tagging status."""
        available_players = self.state_manager.get_available_players()
        tagged_names = set(self.tag_storage.get_tagged_player_names())
        untagged_count = len(available_players) - len(tagged_names)
        
        lines = [
            "=== Player Tagging Status ===",
            f"Total Players: {len(available_players)}",
            f"Tagged: {len(tagged_names)}",
            f"Untagged: {untagged_count}",
            f"Progress: {len(tagged_names)/len(available_players)*100:.1f}%",
            ""
        ]
        
        if untagged_count > 0:
            untagged = [p.name for p in available_players if p.name not in tagged_names]
            lines.append(f"Next {min(10, untagged_count)} untagged players:")
            for i, name in enumerate(untagged[:10], 1):
                lines.append(f"  {i}. {name}")
        
        return "\n".join(lines)
    
    def handle_help(self) -> str:
        """Show help."""
        return """
Available Commands:
  mode <team_selection|live_bid>  - Switch between modes
  select_team <team>               - Select team for team selection mode
  suggest                          - Get grouped recommendations (A/B/C) for selected team
  sell <player> <team> <price>     - Record player sale
  show [team]                      - Show team matrix (or all teams)
  state                            - Show current auction state
  tag <player1> [player2] ...      - Tag 1-10 specific players
  tag_batch [N]                    - Tag next N untagged players (default: 10, max: 10)
  tag_status                        - Show tagging progress
  help                             - Show this help
"""

