# IPL Auction Strategist System

A comprehensive IPL auction strategist system using Google Gemini LLM for intelligent player analysis and team matching, with advanced metrics from cricsheet.org data.

## Features

- **Advanced Metrics**: Compute efscore, winp, and raa phase-wise (Powerplay, Middle Overs, Death) for all players
- **Match Conditions Tracking**: Track performance by wickets fallen and match conditions
- **Bias Modeling**: Model team bias patterns (e.g., Sam Curran effect) based on historical performance
- **Dual Mode Interface**: 
  - Team Selection Mode: Get grouped recommendations (A/B/C) for selected team
  - Live Bid-by-Bid Mode: Real-time recommendations for all teams
- **LLM-Powered Analysis**: Gemini-based player tagging and team matching
- **Real-time State Management**: Instant updates when players are sold

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up Gemini API key:

**Option 1: Using .env file (Recommended)**
```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_api_key_here
```

**Option 2: Using environment variable**
```bash
# Windows PowerShell
$env:GEMINI_API_KEY="your_api_key_here"

# Linux/Mac
export GEMINI_API_KEY=your_api_key_here
```

**Get your API key from:** https://makersuite.google.com/app/apikey

## Usage

### CLI Mode

Run the main application:
```bash
python main.py
```

Available commands:
- `mode <team_selection|live_bid>` - Switch between modes
- `select_team <team>` - Select team for team selection mode
- `suggest` - Get grouped recommendations (A/B/C) for selected team
- `sell <player> <team> <price>` - Record player sale
- `show [team]` - Show team matrix
- `state` - Show current auction state
- `help` - Show help

### API Mode

Start the FastAPI server:
```bash
uvicorn handlers.api_handler:app --reload
```

API endpoints:
- `POST /auction/sell` - Record player sale
- `GET /teams/{team}/matrix` - Get team matrix
- `GET /teams/{team}/recommendations` - Get grouped recommendations
- `GET /state` - Get current auction state
- `GET /live/recommendations` - Get live recommendations for all teams

## Project Structure

```
Cricket_Auction/
├── Data/                    # CSV data files
├── models/                  # Data models
├── core/                    # Core business logic
├── llm/                     # LLM integration
├── scrapers/                # Data scrapers
├── handlers/                # Input/output handlers
├── output/                  # Output generators
├── cache/                   # Cache directories
├── config.py               # Configuration
├── utils.py                # Utilities
├── main.py                 # Main application
└── requirements.txt        # Dependencies
```

## Key Components

### Data Models
- `Player`: Comprehensive player model with advanced metrics and conditions
- `Team`: Team model with home ground conditions
- `AuctionState`: Real-time auction state management
- `U19Player`: U19 player tracking
- `MatchConditions`: Match conditions tracking

### Core Modules
- `data_loader.py`: CSV parser for Supply, RetainedPlayers, PurseBalance
- `state_manager.py`: Real-time state updates
- `metrics_calculator.py`: Advanced metrics (efscore, winp, raa)
- `conditions_analyzer.py`: Match conditions analysis
- `bias_modeler.py`: Team bias modeling
- `playing11_analyzer.py`: Playing 11 gap analysis
- `recommender.py`: Player recommendations
- `player_grouper.py`: A/B/C grouping system

### LLM Integration
- `gemini_client.py`: Gemini API client with caching
- `player_tagger.py`: LLM-based player tagging
- `team_matcher.py`: LLM-based team matching

## Advanced Features

### Phase-wise Metrics
- **efscore**: Expected runs vs actual runs
- **winp**: Win probability added
- **raa**: Runs above average

Computed for Powerplay (overs 1-6), Middle Overs (overs 7-15), and Death (overs 16-20).

### Bias Modeling
Tracks exceptional performances against specific teams (e.g., Sam Curran picking top 3 CSK batters while playing for KXIP, then CSK picking him next auction).

### Match Conditions
Tracks performance by:
- Wickets fallen at entry (0-2, 3-5, 6+)
- Match situation
- Pitch conditions

### Player Grouping
Players are grouped into:
- **Group A**: Perfect fit + High price (primary gap fillers)
- **Group B**: Good fit + Mid-range (secondary gap fillers)
- **Group C**: Backup + Budget (depth options)

## Data Sources

- **CSV Files**: Supply.csv, RetainedPlayers.csv, PurseBalance.csv
- **Cricsheet.org**: Ball-by-ball match data for advanced metrics
- **Authorized Websites**: U19 players from ICC, ESPNcricinfo, etc.

## Configuration

Edit `config.py` to customize:
- Data paths
- Gemini API settings
- Home ground conditions
- Scraping URLs
- Auction rules

## License

This project is for educational purposes.

