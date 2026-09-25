from feeds.provider_factory import ProviderFactory
from detectors.displacement_detector import DisplacementDetector

provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300
)

detector = DisplacementDetector()

events = detector.detect(candles)

print("=" * 60)
print("DISPLACEMENT EVENTS")
print("=" * 60)

for event in events:
    print(event)

print("\nTotal Events:", len(events))

print("\n" + "=" * 60)
print("DISPLACEMENT CHECK")
print("=" * 60)

tests = [
    (150, 180, "BULLISH"),
    (150, 180, "BEARISH"),
    (200, 230, "BULLISH"),
    (230, 260, "BEARISH"),
]

for start, end, direction in tests:

    result = detector.has_displacement(
        candles,
        start,
        end,
        direction
    )

    print(
        f"{direction:8} | {start:3} -> {end:3} | {result}"
    )
