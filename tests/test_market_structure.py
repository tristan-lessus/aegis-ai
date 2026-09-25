from config.settings import API_KEY
from feeds.live_provider import LiveProvider
from detectors.market_structure_detector import MarketStructureDetector


provider = LiveProvider(API_KEY)

candles = provider.get_candles(
    symbol="XAU/USD",
    timeframe="M5",
    count=300,
)

detector = MarketStructureDetector()

swings, breaks = detector.process(candles)

print("=" * 60)
print("SWING POINTS")
print("=" * 60)

for swing in swings:
    print(swing)

print()
print("Total Swings:", len(swings))

print()
print("=" * 60)
print("BREAK OF STRUCTURE")
print("=" * 60)

for structure in breaks:
    print(structure)

print()
print("Total BOS:", len(breaks))
