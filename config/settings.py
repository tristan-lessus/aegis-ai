import os

from dotenv import load_dotenv


load_dotenv()


API_KEY = os.getenv("TWELVE_DATA_API_KEY", "")

DEFAULT_MARKETS = [
    "XAU/USD",
]

ENTRY_TIMEFRAME = "M5"
CONFIRMATION_TIMEFRAME = "M15"
BIAS_TIMEFRAME = "H1"

RISK_PERCENT = 1.0

MIN_CONFIDENCE = 80
