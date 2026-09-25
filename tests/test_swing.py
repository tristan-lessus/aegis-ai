from feeds.provider_factory import ProviderFactory
from detectors.swing_detector import SwingDetector

provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    200
)

detector = SwingDetector(lookback=3)

swings = detector.detect(candles)

classified = detector.classify(swings)

print("=" * 50)
print("SWING DETECTION")
print("=" * 50)

for swing in classified[-20:]:
    print(swing)
