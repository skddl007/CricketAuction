"""REST API handler using FastAPI."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from core.state_manager import StateManager
from core.recommender import Recommender
from core.player_grouper import PlayerGrouper
from output.matrix_generator import MatrixGenerator
from handlers.team_selection_handler import TeamSelectionHandler
from handlers.live_bid_handler import LiveBidHandler
from utils import parse_price_string, normalize_team_name
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# Pydantic models
class SellRequest(BaseModel):
    player_name: str
    team: str
    price: str
    timestamp: Optional[str] = None


class UpdatePlaying11Request(BaseModel):
    team: str
    players: List[str]


class ChatRequest(BaseModel):
    message: str
    team_name: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


# Initialize FastAPI app
app = FastAPI(title="IPL Auction Strategist API")

# Add CORS middleware to allow requests from file:// origin and other origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (including file://)
    allow_credentials=False,  # Must be False when allow_origins=["*"]
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# These will be set during initialization
state_manager: Optional[StateManager] = None
recommender: Optional[Recommender] = None
player_grouper: Optional[PlayerGrouper] = None
matrix_generator: Optional[MatrixGenerator] = None
team_selection_handler: Optional[TeamSelectionHandler] = None
live_bid_handler: Optional[LiveBidHandler] = None
components: Optional[Dict[str, Any]] = None


def initialize_handlers(
    sm: StateManager,
    rec: Recommender,
    pg: PlayerGrouper,
    mg: MatrixGenerator
):
    """Initialize handlers with dependencies."""
    global state_manager, recommender, player_grouper, matrix_generator
    global team_selection_handler, live_bid_handler
    
    print("=" * 60)
    print("[API_HANDLER] Initializing handlers...")
    print(f"[API_HANDLER] StateManager: {sm is not None}")
    print(f"[API_HANDLER] Recommender: {rec is not None}")
    print(f"[API_HANDLER] PlayerGrouper: {pg is not None}")
    print(f"[API_HANDLER] MatrixGenerator: {mg is not None}")
    
    state_manager = sm
    recommender = rec
    player_grouper = pg
    matrix_generator = mg
    team_selection_handler = TeamSelectionHandler(sm, rec, pg)
    live_bid_handler = LiveBidHandler(sm, rec, pg)
    
    print(f"[API_HANDLER] TeamSelectionHandler: {team_selection_handler is not None}")
    print(f"[API_HANDLER] LiveBidHandler: {live_bid_handler is not None}")
    print("[API_HANDLER] Handlers initialized successfully!")
    print("=" * 60)


def set_components(comps: Dict[str, Any]):
    """Set global components for chat handler."""
    global components
    components = comps


@app.post("/auction/sell")
async def sell_player(request: SellRequest):
    """Record player sale."""
    if not state_manager:
        raise HTTPException(status_code=500, detail="State manager not initialized")
    
    price = parse_price_string(request.price)
    if not price:
        raise HTTPException(status_code=400, detail=f"Invalid price: {request.price}")
    
    team_name = normalize_team_name(request.team)
    
    try:
        state_manager.sell_player(request.player_name, team_name, price, request.timestamp)
        return {"status": "success", "message": f"{request.player_name} sold to {team_name}"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/teams/{team}/matrix")
async def get_team_matrix(team: str):
    """Get team matrix."""
    if not matrix_generator:
        raise HTTPException(status_code=500, detail="Matrix generator not initialized")
    
    team_name = normalize_team_name(team)
    team_obj = state_manager.get_team(team_name) if state_manager else None
    
    if not team_obj:
        raise HTTPException(status_code=404, detail=f"Team {team_name} not found")
    
    return {"matrix": matrix_generator.generate_team_matrix(team_obj)}


@app.get("/teams/{team}/recommendations")
async def get_team_recommendations(team: str, group: Optional[str] = None):
    """Get grouped recommendations for a team (includes gap analysis first)."""
    print("\n" + "=" * 60)
    print(f"[API] GET /teams/{team}/recommendations")
    print(f"[API] Group filter: {group}")
    print(f"[API] TeamSelectionHandler exists: {team_selection_handler is not None}")
    print(f"[API] StateManager exists: {state_manager is not None}")
    
    if not team_selection_handler or not state_manager:
        print("[API] ERROR: Handler not initialized!")
        raise HTTPException(status_code=500, detail="Handler not initialized")
    
    from core.playing11_analyzer import Playing11Analyzer
    
    team_name = normalize_team_name(team)
    print(f"[API] Normalized team name: {team_name}")
    
    team_obj = state_manager.get_team(team_name)
    print(f"[API] Team object found: {team_obj is not None}")
    
    if not team_obj:
        print(f"[API] ERROR: Team {team_name} not found")
        raise HTTPException(status_code=404, detail=f"Team {team_name} not found")
    
    # First, analyze gaps and weak points
    print("[API] Analyzing team gaps...")
    analyzer = Playing11Analyzer()
    gap_analysis = analyzer.analyze_team(team_obj)
    print(f"[API] Gap analysis complete. Total gaps: {gap_analysis.get('gaps', {}).get('total_gaps', 0)}")
    
    # Then get recommendations
    print("[API] Getting team recommendations...")
    result = team_selection_handler.get_team_recommendations(team, filter_group=group)
    print(f"[API] Recommendations result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
    print(f"[API] Result has error: {result.get('error') if isinstance(result, dict) else 'N/A'}")
    
    if result.get('error'):
        print(f"[API] ERROR in result: {result['error']}")
        raise HTTPException(status_code=404, detail=result['error'])
    
    # Add gap analysis to result
    result['gap_analysis'] = {
        'weak_points': gap_analysis.get('weak_points', []),
        'batting_order_gaps': [
            bo for bo in gap_analysis.get('batting_order', []) 
            if bo.get('status') == 'NotCheck'
        ],
        'bowling_phase_gaps': [
            bp for bp in gap_analysis.get('bowling_phases', []) 
            if bp.get('status') == 'NotCheck'
        ],
        'total_gaps': gap_analysis['gaps'].get('total_gaps', 0)
    }
    
    # Log result summary
    if isinstance(result, dict) and 'groups' in result:
        groups = result.get('groups', {})
        print(f"[API] Groups returned: {list(groups.keys())}")
        for group_name, group_data in groups.items():
            count = len(group_data) if isinstance(group_data, list) else 0
            print(f"[API]   Group {group_name}: {count} recommendations")
    
    print(f"[API] Returning result with {len(result)} keys")
    print("=" * 60 + "\n")
    
    return result


@app.get("/state")
async def get_state():
    """Get current auction state."""
    if not state_manager:
        raise HTTPException(status_code=500, detail="State manager not initialized")
    
    return {
        "supply_count": state_manager.get_supply_count(),
        "sold_count": len(state_manager.get_sold_players()),
        "teams": {name: team.to_dict() for name, team in state_manager.get_all_teams().items()}
    }


@app.get("/live/recommendations")
async def get_live_recommendations():
    """Get live recommendations for all teams."""
    if not live_bid_handler:
        raise HTTPException(status_code=500, detail="Handler not initialized")
    
    recommendations = live_bid_handler.get_all_teams_recommendations()
    return {"recommendations": recommendations}


@app.get("/teams/{team}/gaps")
async def get_team_gaps(team: str):
    """Get detailed gap analysis and weak points for a team."""
    if not state_manager:
        raise HTTPException(status_code=500, detail="State manager not initialized")
    
    from core.playing11_analyzer import Playing11Analyzer
    
    team_name = normalize_team_name(team)
    team_obj = state_manager.get_team(team_name)
    
    if not team_obj:
        raise HTTPException(status_code=404, detail=f"Team {team_name} not found")
    
    analyzer = Playing11Analyzer()
    analysis = analyzer.analyze_team(team_obj)
    
    return {
        "team": team_name,
        "analysis": analysis,
        "summary": {
            "total_gaps": analysis['gaps'].get('total_gaps', 0),
            "weak_points_count": len(analysis.get('weak_points', [])),
            "critical_weak_points": [
                wp for wp in analysis.get('weak_points', []) 
                if wp.get('severity') == 'Critical'
            ],
            "purse_available_cr": analysis.get('purse_available_cr', 0),
            "available_slots": analysis.get('available_slots', 0)
        }
    }


@app.get("/teams/{team}/weak-points")
async def get_team_weak_points(team: str):
    """Get weak points and gaps for a team (simplified endpoint)."""
    if not state_manager:
        raise HTTPException(status_code=500, detail="State manager not initialized")
    
    from core.playing11_analyzer import Playing11Analyzer
    
    team_name = normalize_team_name(team)
    team_obj = state_manager.get_team(team_name)
    
    if not team_obj:
        raise HTTPException(status_code=404, detail=f"Team {team_name} not found")
    
    analyzer = Playing11Analyzer()
    analysis = analyzer.analyze_team(team_obj)
    
    return {
        "team": team_name,
        "weak_points": analysis.get('weak_points', []),
        "batting_order_gaps": [
            bo for bo in analysis.get('batting_order', []) 
            if bo.get('status') == 'NotCheck'
        ],
        "bowling_phase_gaps": [
            bp for bp in analysis.get('bowling_phases', []) 
            if bp.get('status') == 'NotCheck'
        ],
        "purse_available_cr": analysis.get('purse_available_cr', 0)
    }


@app.post("/chat")
async def chat_with_recommender(request: ChatRequest):
    """Chat with the recommender system."""
    print("\n" + "=" * 60)
    print(f"[API] POST /chat")
    print(f"[API] Message: {request.message[:100]}..." if len(request.message) > 100 else f"[API] Message: {request.message}")
    print(f"[API] Team name: {request.team_name}")
    print(f"[API] Components exists: {components is not None}")
    
    if not components:
        print("[API] ERROR: System components not initialized!")
        raise HTTPException(status_code=500, detail="System components not initialized")
    
    from llm.gemini_client import GeminiClient
    from llm.prompt_loader import PromptLoader
    from core.playing11_analyzer import Playing11Analyzer
    
    gemini_client = components.get('gemini_client')
    print(f"[API] GeminiClient exists: {gemini_client is not None}")
    
    if not gemini_client:
        print("[API] ERROR: Gemini client not available!")
        raise HTTPException(
            status_code=503, 
            detail="LLM features not available. GEMINI_API_KEY required."
        )
    
    print("[API] Loading prompt...")
    prompt_loader = PromptLoader()
    system_prompt = prompt_loader.get_full_context()
    print(f"[API] System prompt loaded: {len(system_prompt)} characters")
    
    # Build context based on request
    context_parts = []
    
    # If team specified, include team analysis
    if request.team_name:
        print(f"[API] Processing team context for: {request.team_name}")
        team_name = normalize_team_name(request.team_name)
        team = state_manager.get_team(team_name) if state_manager else None
        print(f"[API] StateManager exists: {state_manager is not None}")
        print(f"[API] Team found: {team is not None}")
        
        if team:
            print("[API] Analyzing team...")
            analyzer = Playing11Analyzer()
            team_analysis = analyzer.analyze_team(team)
            print(f"[API] Team analysis complete. Weak points: {len(team_analysis.get('weak_points', []))}")
            
            context_parts.append(f"Team: {team_name}")
            context_parts.append(f"Purse Available: {team_analysis.get('purse_available_cr', 0):.2f} Cr")
            context_parts.append(f"Available Slots: {team_analysis.get('available_slots', 0)}")
            context_parts.append(f"\nWeak Points:")
            for wp in team_analysis.get('weak_points', []):
                context_parts.append(f"- {wp['category']} ({wp['severity']}): {wp['details']}")
            context_parts.append(f"\nBatting Order Gaps:")
            for bo in team_analysis.get('batting_order', []):
                if bo.get('status') == 'NotCheck':
                    context_parts.append(f"- Position {bo['position']}: Need {bo.get('speciality', 'Player')}")
            context_parts.append(f"\nBowling Phase Gaps:")
            for bp in team_analysis.get('bowling_phases', []):
                if bp.get('status') == 'NotCheck':
                    context_parts.append(f"- {bp['phase']}: Need primary bowler")
            print(f"[API] Context parts added: {len(context_parts)} items")
        else:
            print(f"[API] WARNING: Team {team_name} not found in state manager")
    
    # Add custom context if provided
    if request.context:
        print(f"[API] Adding custom context: {request.context}")
        context_parts.append(f"\nAdditional Context: {request.context}")
    
    context_str = "\n".join(context_parts) if context_parts else ""
    print(f"[API] Total context length: {len(context_str)} characters")
    
    # Build chat prompt
    chat_prompt = f"""{system_prompt}

=== USER QUERY ===
{request.message}

{context_str}

=== YOUR ROLE ===
You are an IPL auction strategist assistant. Help the user with:
1. Analyzing team gaps and weak points
2. Recommending players based on identified gaps
3. Explaining auction strategies
4. Answering questions about player-team fits

Provide clear, actionable advice based on the team's current state and requirements.
"""
    
    print(f"[API] Total prompt length: {len(chat_prompt)} characters")
    print("[API] Calling Gemini API...")
    
    try:
        response = gemini_client.generate_content(chat_prompt)
        print(f"[API] Gemini response received: {len(response) if response else 0} characters")
        print(f"[API] Response preview: {response[:100] if response else 'None'}...")
        
        result = {
            "response": response,
            "team": request.team_name,
            "context_provided": bool(context_parts)
        }
        print("[API] Chat response successful!")
        print("=" * 60 + "\n")
        return result
    except Exception as e:
        print(f"[API] ERROR generating response: {str(e)}")
        print(f"[API] Exception type: {type(e).__name__}")
        import traceback
        print(f"[API] Traceback: {traceback.format_exc()}")
        print("=" * 60 + "\n")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

