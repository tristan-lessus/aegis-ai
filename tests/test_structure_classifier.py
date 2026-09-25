from config.settings import API_KEY
from feeds.live_provider import LiveProvider

from detectors.swing_detector import SwingDetector
from detectors.structure_classifier import StructureClassifier

provider = LiveProvider(API_KEY)

candles = provider.get_candles(
    symbol="XAU/USD",
    timeframe="M5",
    count=300,
)

swings = SwingDetector().detect(candles)

classified = StructureClassifier().classify(swings)

print("=" * 80)

for s in classified:
    print(
        f"{s['time']} | {s['label']:2} | {s['price']:.2f}"
    )

print()
print("Total:", len(classified))
