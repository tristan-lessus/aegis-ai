from feeds.provider_factory import ProviderFactory
from detectors.swing_detector import SwingDetector
from detectors.liquidity_detector import LiquidityDetector

provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300
)

detector = SwingDetector()

swings = detector.detect(candles)

liquidity = LiquidityDetector()

zones = liquidity.detect(swings)

zones = liquidity.detect_sweeps(
    zones,
    candles
)

print("=" * 60)
print("LIQUIDITY")
print("=" * 60)

for zone in zones:
    print(zone)
