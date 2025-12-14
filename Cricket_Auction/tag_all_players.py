"""Automated script to tag all players in batches of 10."""

import os
import sys
import time
from pathlib import Path

# Change to script directory to ensure relative paths work
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Add current directory to path
sys.path.insert(0, str(script_dir))

from config import GEMINI_API_KEY, GEMINI_MODEL, DATA_DIR
from core.data_loader import load_all_data
from core.state_manager import StateManager
from core.player_tag_storage import PlayerTagStorage
from models.auction_state import AuctionState
from llm.gemini_client import GeminiClient
from llm.player_tagger import PlayerTagger


def initialize_tagging_system():
    """Initialize system components for tagging."""
    print("=" * 60)
    print("IPL Player Tagging System - Automated Batch Processing")
    print("=" * 60)
    print()
    
    # Check API key
    if not GEMINI_API_KEY:
        print("[ERROR] GEMINI_API_KEY not set!")
        print("Please set it in .env file or as environment variable.")
        print("See ENV_SETUP.md for instructions.")
        return None
    
    # Initialize tag storage
    tag_storage = PlayerTagStorage()
    print(f"[OK] Tag storage initialized: {tag_storage.csv_path}")
    
    # Load data
    print("\nLoading data from CSV files...")
    players, teams = load_all_data(str(DATA_DIR))
    print(f"[OK] Loaded {len(players)} players and {len(teams)} teams")
    
    # Check existing tagged players
    tagged_players = tag_storage.load_players()
    tagged_names = set(tag_storage.get_tagged_player_names())
    print(f"[OK] Found {len(tagged_names)} already tagged players")
    
    # Initialize Gemini client
    print("\nInitializing Gemini client...")
    try:
        gemini_client = GeminiClient(api_key=GEMINI_API_KEY, model_name=GEMINI_MODEL)
        print("[OK] Gemini client initialized")
    except Exception as e:
        print(f"[ERROR] Could not initialize Gemini client: {e}")
        return None
    
    # Initialize player tagger
    player_tagger = PlayerTagger(gemini_client)
    print("[OK] Player tagger initialized")
    
    # Get untagged players
    untagged_players = [p for p in players if p.name not in tagged_names]
    print(f"\n[STATUS] {len(tagged_names)}/{len(players)} players tagged ({len(tagged_names)/len(players)*100:.1f}%)")
    print(f"[INFO] Remaining: {len(untagged_players)} players to tag")
    
    if not untagged_players:
        print("\n[SUCCESS] All players are already tagged!")
        return None
    
    return {
        'tag_storage': tag_storage,
        'player_tagger': player_tagger,
        'untagged_players': untagged_players,
        'total_players': len(players),
        'tagged_count': len(tagged_names)
    }


def tag_batch(players, player_tagger, tag_storage, batch_num, total_batches):
    """Tag a batch of players (up to 10) in a single LLM call."""
    print(f"\n{'=' * 60}")
    print(f"Batch {batch_num}/{total_batches} - Tagging {len(players)} players")
    print(f"{'=' * 60}")
    print(f"\n[SENDING] Sending {len(players)} players to LLM in one batch call...")
    
    # Show players being tagged
    for i, player in enumerate(players, 1):
        print(f"  {i}. {player.name} ({player.country}) - {player.base_price}L")
    
    tagged_players = []
    errors = []
    
    try:
        # Tag all players in a single LLM call
        tagged_players = player_tagger.tag_players_batch(players)
        
        # Show results
        print(f"\n[RESULTS] Received tags for {len(tagged_players)} players:")
        for i, tagged_player in enumerate(tagged_players, 1):
            role = tagged_player.primary_role.value if tagged_player.primary_role else "N/A"
            quality = tagged_player.quality.value if tagged_player.quality else "N/A"
            
            # Show advanced metrics if available
            metrics_info = ""
            if tagged_player.advanced_metrics:
                pp = tagged_player.advanced_metrics.powerplay or {}
                if pp.get('efscore'):
                    metrics_info = f" | PP-efscore: {pp.get('efscore', 0):.1f}"
            
            print(f"  {i}. {tagged_player.name}: {role} | Quality: Tier {quality}{metrics_info}")
        
    except Exception as e:
        error_msg = f"Error in batch tagging: {str(e)}"
        print(f"    [ERROR] {error_msg}")
        errors.append(error_msg)
        # Fallback: try individual tagging
        print(f"\n[FALLBACK] Attempting individual tagging...")
        for player in players:
            try:
                tagged_player = player_tagger.tag_player(player)
                tagged_players.append(tagged_player)
                role = tagged_player.primary_role.value if tagged_player.primary_role else "N/A"
                print(f"  [OK] {player.name}: {role}")
                time.sleep(0.2)  # Rate limiting
            except Exception as e2:
                error_msg = f"Error tagging {player.name}: {str(e2)}"
                print(f"  [ERROR] {error_msg}")
                errors.append(error_msg)
                continue
    
    # Save batch to CSV
    if tagged_players:
        try:
            tag_storage.save_players(tagged_players, append=True)
            print(f"\n[OK] Saved {len(tagged_players)} players to CSV")
        except Exception as e:
            print(f"\n[ERROR] Error saving to CSV: {str(e)}")
            errors.append(f"CSV save error: {str(e)}")
    
    return {
        'tagged': len(tagged_players),
        'errors': len(errors),
        'error_details': errors
    }


def main():
    """Main function to tag all players."""
    # Initialize system
    system = initialize_tagging_system()
    if not system:
        return
    
    tag_storage = system['tag_storage']
    player_tagger = system['player_tagger']
    untagged_players = system['untagged_players']
    total_players = system['total_players']
    tagged_count = system['tagged_count']
    
    # Process in batches of 10
    batch_size = 10
    total_batches = (len(untagged_players) + batch_size - 1) // batch_size
    
    print(f"\n[START] Starting automated tagging process...")
    print(f"   Batch size: {batch_size} players")
    print(f"   Total batches: {total_batches}")
    print(f"   Estimated time: ~{total_batches * 30} seconds (30s per batch)")
    print()
    
    # Auto-start after 2 seconds (can be interrupted with Ctrl+C)
    try:
        print("Starting in 2 seconds... (Press Ctrl+C to cancel)")
        time.sleep(2)
    except KeyboardInterrupt:
        print("\n[CANCELLED] Process cancelled by user")
        return
    print()
    
    total_tagged = 0
    total_errors = 0
    
    try:
        for batch_num in range(1, total_batches + 1):
            # Get batch
            start_idx = (batch_num - 1) * batch_size
            end_idx = start_idx + batch_size
            batch = untagged_players[start_idx:end_idx]
            
            # Tag batch
            result = tag_batch(batch, player_tagger, tag_storage, batch_num, total_batches)
            
            total_tagged += result['tagged']
            total_errors += result['errors']
            
            # Update progress
            current_tagged = tagged_count + total_tagged
            progress = (current_tagged / total_players) * 100
            
            print(f"\n[PROGRESS] {current_tagged}/{total_players} players tagged ({progress:.1f}%)")
            print(f"   [OK] Tagged this batch: {result['tagged']}")
            if result['errors'] > 0:
                print(f"   [ERROR] Errors this batch: {result['errors']}")
            
            # Show errors if any
            if result['error_details']:
                print("\n   Error details:")
                for err in result['error_details']:
                    print(f"     - {err}")
            
            # Pause between batches (except last)
            if batch_num < total_batches:
                print(f"\n[WAIT] Waiting 2 seconds before next batch...")
                time.sleep(2)
        
        # Final summary
        print(f"\n{'=' * 60}")
        print("[SUCCESS] TAGGING COMPLETE!")
        print(f"{'=' * 60}")
        print(f"Total players: {total_players}")
        print(f"Previously tagged: {tagged_count}")
        print(f"Newly tagged: {total_tagged}")
        print(f"Total tagged now: {tagged_count + total_tagged}")
        print(f"Errors: {total_errors}")
        print(f"Success rate: {((total_tagged - total_errors) / len(untagged_players) * 100):.1f}%")
        print(f"\n[INFO] Tagged data saved to: {tag_storage.csv_path}")
        print()
        
    except KeyboardInterrupt:
        print(f"\n\n[WARNING] Process interrupted by user")
        print(f"   Progress saved: {tagged_count + total_tagged}/{total_players} players tagged")
        print(f"   You can resume by running this script again")
        print(f"   (Already tagged players will be skipped)")
        print()


if __name__ == "__main__":
    main()

