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
    
    print("\n" + "=" * 60)
    print("SYSTEM INITIALIZATION SUMMARY")
    print("=" * 60)
    print(f"StateManager: {state_manager is not None}")
    print(f"GeminiClient: {gemini_client is not None}")
    print(f"Recommender: {recommender is not None}")
    print(f"PlayerGrouper: {player_grouper is not None}")
    print(f"TeamSelectionHandler: {team_selection_handler is not None}")
    print(f"LiveBidHandler: {live_bid_handler is not None}")
    
    if state_manager:
        teams = state_manager.get_all_teams()
        available = state_manager.get_available_players()
        print(f"Teams loaded: {len(teams)}")
        print(f"Available players: {len(available)}")
        print(f"Team names: {list(teams.keys())}")
    
    print("=" * 60)
    print("System initialized successfully!")
    print("=" * 60 + "\n")
    
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
    # Server is intended to be run via an ASGI server (uvicorn/gunicorn).
    # When running programmatically (python main.py) the `__main__` block
    # will start a uvicorn server. When using `uvicorn main:app`, the
    # FastAPI `startup` event will initialize the system automatically.
    print("Server mode selected. Use an ASGI server to run the app (uvicorn main:app ...)")
    print(f"Server will run on http://{API_HOST}:{API_PORT} when started by an ASGI server")


def main():
    """Main entry point."""
    import sys
    # When called directly (python main.py) initialize system and either
    # run CLI or start an ASGI server. When used as an import target for
    # an ASGI server (uvicorn main:app) this function should not be
    # invoked by the server; instead the FastAPI `startup` handler will
    # perform initialization.

    components = initialize_system()

    # Initialize API handlers so the app is ready when run directly
    from handlers.api_handler import initialize_handlers, set_components
    initialize_handlers(
        components['state_manager'],
        components['recommender'],
        components['player_grouper'],
        components['matrix_generator']
    )
    set_components(components)

    # CLI or programmatic server
    if len(sys.argv) > 1 and sys.argv[1] == '--cli':
        run_cli_mode(components)
    else:
        # Start uvicorn programmatically when running as a script
        import uvicorn
        print(f"Starting uvicorn server on http://{API_HOST}:{API_PORT}")
        uvicorn.run("main:app", host=API_HOST, port=API_PORT, reload=False)


# Expose FastAPI app for ASGI servers and initialize on startup
from handlers.api_handler import app as app


@app.on_event("startup")
async def _initialize_on_startup():
    """Initialize system when ASGI server starts the app."""
    try:
        components = initialize_system()
        from handlers.api_handler import initialize_handlers, set_components
        initialize_handlers(
            components['state_manager'],
            components['recommender'],
            components['player_grouper'],
            components['matrix_generator']
        )
        set_components(components)
    except Exception as e:
        # Log any startup failure; raising will stop the ASGI server startup
        print(f"Startup initialization failed: {e}")


if __name__ == "__main__":
    main()

