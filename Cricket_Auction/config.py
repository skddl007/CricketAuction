"""Configuration file for IPL Auction Strategist System."""

import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip .env loading
    pass

# Data paths - use absolute path based on project root
PROJECT_ROOT = Path(__file__).parent
DATA_DIR = PROJECT_ROOT / "Data"
SUPPLY_CSV = DATA_DIR / "Supply.csv"
RETAINED_PLAYERS_CSV = DATA_DIR / "RetainedPlayers.csv"
PURSE_BALANCE_CSV = DATA_DIR / "PurseBalance.csv"

# Cache directories - use absolute path based on project root
CACHE_DIR = PROJECT_ROOT / "cache"
LLM_CACHE_DIR = CACHE_DIR / "llm"
CRICSHEET_CACHE_DIR = CACHE_DIR / "cricsheet"
SCRAPED_DATA_CACHE_DIR = CACHE_DIR / "scraped"

# Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
# Valid model names: gemini-pro, gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash-exp
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# Auction rules
MAX_SQUAD_SIZE = 25
MAX_FOREIGN_PLAYERS = 8
MIN_SQUAD_SIZE = 18

# Home ground conditions
HOME_GROUNDS = {
    'CSK': ('Chepauk', 'spin-friendly'),
    'RCB': ('Chinnaswamy', 'batting-friendly'),
    'MI': ('Wankhede', 'pace-friendly'),
    'KKR': ('Eden Gardens', 'balanced'),
    'DC': ('Arun Jaitley', 'balanced'),
    'GT': ('Ahmedabad', 'pace-friendly'),
    'LSG': ('Lucknow', 'balanced'),
    'PBKS': ('Mohali', 'pace-friendly'),
    'RR': ('Jaipur', 'balanced'),
    'SRH': ('Hyderabad', 'balanced')
}

# Scraping URLs
IPL_URLS = {
    'official': 'https://www.iplt20.com/',
    'espncricinfo_2023': 'https://www.espncricinfo.com/series/indian-premier-league-2023-1345038',
    'espncricinfo_2024': 'https://www.espncricinfo.com/series/indian-premier-league-2024-1410320',
    'espncricinfo_2025': 'https://www.espncricinfo.com/series/ipl-2025-1449924',
    'cricbuzz_2023': 'https://www.cricbuzz.com/cricket-series/5945/indian-premier-league-2023',
    'cricbuzz_2024': 'https://www.cricbuzz.com/cricket-series/7607/indian-premier-league-2024/matches',
    'cricbuzz_2025': 'https://www.cricbuzz.com/cricket-series/9237/indian-premier-league-2025'
}

SMAT_URL = 'https://www.espncricinfo.com/series/syed-mushtaq-ali-trophy-2025-26-1492382'

# Cricsheet.org
CRICSHEET_BASE_URL = 'https://cricsheet.org/matches/'
CRICSHEET_COMPETITIONS = ['ipl', 'smat', 'bbl', 'sa20', 'cpl']

# U19 data sources
U19_SOURCES = [
    'https://www.icc-cricket.com/u19-world-cup',
    'https://www.espncricinfo.com/cricket/u19-world-cup',
    'https://www.bcci.tv',
    'https://www.cricket.com.au',
    'https://www.ecb.co.uk'
]

# API settings
API_HOST = "127.0.0.1"  # localhost only
API_PORT = 8000

# Rate limiting
LLM_RATE_LIMIT_REQUESTS_PER_MINUTE = 60
LLM_MIN_REQUEST_INTERVAL = 0.1

