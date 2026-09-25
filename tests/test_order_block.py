from feeds.provider_factory import ProviderFactory
from detectors.order_block_detector import OrderBlockDetector

provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300
)

detector = OrderBlockDetector()

blocks = detector.process(candles)

print("=" * 60)
print("ORDER BLOCKS")
print("=" * 60)

for block in blocks:
    print(block)

print("\nTotal:", len(blocks))
print("Fresh:", len(detector.get_unmitigated(blocks)))
