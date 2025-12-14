"""Main application for IPL Auction Strategist System."""

import os
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from config import GEMINI_API_KEY, GEMINI_MODEL, DATA_DIR, API_HOST, API_PORT
from core.data_loader import load_all_data
from core.state_manager import StateManager
from core.player_tag_storage import PlayerTagStorage
from models.auction_state import AuctionState
from llm.gemini_client import GeminiClient
from llm.player_tagger import PlayerTagger
from llm.team_matcher import TeamMatcher
from core.bias_modeler import BiasModeler
from core.bias_integrator import BiasIntegrator
from core.recommender import Recommender
from core.player_grouper import PlayerGrouper
from output.matrix_generator import MatrixGenerator
from handlers.cli_handler import CLIHandler
from handlers.live_bid_handler import LiveBidHandler
from handlers.team_selection_handler import TeamSelectionHandler


def initialize_system():
    """Initialize the entire system."""
    print("Initializing IPL Auction Strategist System...")
    
    # Initialize tag storage
    tag_storage = PlayerTagStorage()
    
    # Load data
    print("Loading data from CSV files...")
    print(f"Data directory: {DATA_DIR}")
    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Data directory not found at {DATA_DIR}. "
            f"Please ensure the Data folder exists in the project root."
        )
    players, teams = load_all_data(DATA_DIR)
    print(f"Loaded {len(players)} players and {len(teams)} teams")
    
    # Load tagged players if available
    tagged_players = tag_storage.load_players()
    if tagged_players:
        print(f"Loading {len(tagged_players)} tagged players from CSV...")
        # Merge tagged data with existing players
        tagged_dict = {p.name: p for p in players}
        for name, tagged_player in tagged_players.items():
            if name in tagged_dict:
                # Update existing player with tagged data
                existing = tagged_dict[name]
                # Copy tagged attributes
                existing.primary_role = tagged_player.primary_role
                existing.batting_role = tagged_player.batting_role
                existing.bowling_role = tagged_player.bowling_role
                existing.speciality = tagged_player.speciality
                existing.quality = tagged_player.quality
                existing.bat_utilization = tagged_player.bat_utilization
                existing.bowl_utilization = tagged_player.bowl_utilization
                existing.international_leagues = tagged_player.international_leagues
                existing.ipl_experience = tagged_player.ipl_experience
                existing.scouting = tagged_player.scouting
                existing.smat_performance = tagged_player.smat_performance
                existing.advanced_metrics = tagged_player.advanced_metrics
                existing.metadata.update(tagged_player.metadata)
        print(f"✓ Merged tagged data for {len(tagged_players)} players")
    
    # Create auction state
    auction_state = AuctionState()
    auction_state.available_players = players
    auction_state.teams = teams
    
    # Create state manager
    state_manager = StateManager(auction_state)
    
    # Initialize Gemini client (if API key available)
    gemini_client = None
    if GEMINI_API_KEY:
        try:
            gemini_client = GeminiClient(api_key=GEMINI_API_KEY, model_name=GEMINI_MODEL)
            print("Gemini client initialized")
        except Exception as e:
            print(f"Warning: Could not initialize Gemini client: {e}")
            print("LLM features will be limited")
    else:
        print("Warning: GEMINI_API_KEY not set. LLM features will be disabled.")
    
    # Initialize components
    bias_modeler = BiasModeler()
    bias_integrator = BiasIntegrator(bias_modeler) if gemini_client else None
    
    player_tagger = PlayerTagger(gemini_client) if gemini_client else None
    team_matcher = TeamMatcher(gemini_client, bias_integrator) if gemini_client and bias_integrator else None
    
    recommender = Recommender(team_matcher) if team_matcher else None
    player_grouper = PlayerGrouper(recommender) if recommender else None
    matrix_generator = MatrixGenerator(state_manager)
    
    # Initialize handlers
    cli_handler = CLIHandler(
        state_manager, 
        recommender, 
        player_grouper, 
        matrix_generator,
        player_tagger=player_tagger,
        tag_storage=tag_storage
    ) if matrix_generator else None
    live_bid_handler = LiveBidHandler(state_manager, recommender, player_grouper) if recommender and player_grouper else None
    team_selection_handler = TeamSelectionHandler(state_manager, recommender, player_grouper) if recommender and player_grouper else None
    
    print("System initialized successfully!")
    
    return {
        'state_manager': state_manager,
        'gemini_client': gemini_client,
        'bias_modeler': bias_modeler,
        'bias_integrator': bias_integrator,
        'player_tagger': player_tagger,
        'team_matcher': team_matcher,
        'recommender': recommender,
        'player_grouper': player_grouper,
        'matrix_generator': matrix_generator,
        'tag_storage': tag_storage,
        'cli_handler': cli_handler,
        'live_bid_handler': live_bid_handler,
        'team_selection_handler': team_selection_handler
    }


def run_cli_mode(components):
    """Run CLI mode."""
    cli_handler = components.get('cli_handler')
    if not cli_handler:
        print("CLI handler not available.")
        print("Note: Basic commands work, but LLM features require GEMINI_API_KEY")
        return
    
    print("\n=== IPL Auction Strategist System ===")
    print("Type 'help' for available commands")
    print("Type 'exit' to quit\n")
    
    while True:
        try:
            command = input("> ").strip()
            if command.lower() == 'exit':
                break
            
            if command:
                result = cli_handler.handle_command(command)
                print(result)
                print()
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


def run_server_mode(components):
    """Run server mode with FastAPI."""
    import uvicorn
    from handlers.api_handler import initialize_handlers
    
    # Initialize API handlers
    initialize_handlers(
        components['state_manager'],
        components['recommender'],
        components['player_grouper'],
        components['matrix_generator']
    )
    
    # Store components globally for chat handler
    from handlers.api_handler import set_components
    set_components(components)
    
    print(f"\n=== Starting IPL Auction Strategist Server ===")
    print(f"Server will run on http://{API_HOST}:{API_PORT}")
    print(f"API docs available at http://{API_HOST}:{API_PORT}/docs")
    print(f"Press Ctrl+C to stop\n")
    
    uvicorn.run(
        "handlers.api_handler:app",
        host=API_HOST,
        port=API_PORT,
        reload=False
    )


def main():
    """Main entry point."""
    import sys
    
    # Initialize system
    components = initialize_system()
    
    # Check if CLI mode is requested, otherwise run server mode by default
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        # Run CLI mode
        run_cli_mode(components)
    else:
        # Run server mode by default
        run_server_mode(components)


if __name__ == "__main__":
    main()

