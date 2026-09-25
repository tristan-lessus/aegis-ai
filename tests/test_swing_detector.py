from config.settings import API_KEY
from feeds.live_provider import LiveProvider
from detectors.swing_detector import SwingDetector

provider = LiveProvider(API_KEY)

candles = provider.get_candles(
    symbol="XAU/USD",
    timeframe="M5",
    count=300,
)

detector = SwingDetector(lookback=3)

swings = detector.detect(candles)

print("=" * 60)
print("SWINGS")
print("=" * 60)

for swing in swings:
    print(swing)

print()
print("Total Swings:", len(swings))
