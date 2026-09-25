from feeds.provider_factory import ProviderFactory
from detectors.swing_detector import SwingDetector
from detectors.market_structure import MarketStructure

provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300
)

swings = SwingDetector(3).classify(
    SwingDetector(3).detect(candles)
)

structure = MarketStructure()

events = structure.analyze(swings)

print("=" * 60)
print("MARKET STRUCTURE")
print("=" * 60)

for event in events:
    print(event)

print("\nCurrent Trend:", structure.trend)
