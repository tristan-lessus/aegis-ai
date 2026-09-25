from config.settings import API_KEY

from feeds.live_provider import LiveProvider

from detectors.market_structure_detector import MarketStructureDetector
from detectors.external_structure import ExternalStructure
from detectors.structure_classifier import StructureClassifier
from detectors.bos_detector import BOSDetector


provider = LiveProvider(API_KEY)

candles = provider.get_candles(
    symbol="XAU/USD",
    timeframe="M5",
    count=300,
)

# Detect raw swings
swings, _ = MarketStructureDetector().process(candles)

print("=" * 60)
print("RAW SWINGS")
print("=" * 60)

for swing in swings:
    print(swing)

print()
print("Total Raw Swings:", len(swings))

# Filter external swings
swings = ExternalStructure().filter(swings)

print()
print("=" * 60)
print("FILTERED SWINGS")
print("=" * 60)

for swing in swings:
    print(swing)

print()
print("Total Filtered Swings:", len(swings))

# Classify market structure
classified = StructureClassifier().classify(swings)

print()
print("=" * 60)
print("CLASSIFIED SWINGS")
print("=" * 60)

for swing in classified:
    print(
        f"{swing['time']} | "
        f"{swing['label']} | "
        f"{swing['price']:.2f}"
    )

print()
print("Total Classified:", len(classified))

# Detect BOS / CHOCH
events = BOSDetector().detect(classified)

print()
print("=" * 60)
print("MARKET STRUCTURE")
print("=" * 60)

for event in events:
    print(
        f"{event.time} | "
        f"{event.direction} | "
        f"{event.event} | "
        f"{event.price:.2f}"
    )

print()
print("Total Events:", len(events))
