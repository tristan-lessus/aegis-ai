from feeds.provider_factory import ProviderFactory
from detectors.internal_structure_detector import InternalStructureDetector


provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300
)

detector = InternalStructureDetector()

events = detector.detect(candles)

print("=" * 60)
print("INTERNAL MARKET STRUCTURE")
print("=" * 60)

if not events:
    print("No Internal Structure Found")

for event in events:

    print(
        f"{event.time} | "
        f"{event.direction:<8} | "
        f"{event.event:<5} | "
        f"{round(event.price,2)}"
    )

print()
print("Total Events:", len(events))

if events:
    latest = events[-1]

    print()
    print("=" * 60)
    print("LATEST INTERNAL STRUCTURE")
    print("=" * 60)
    print("Time      :", latest.time)
    print("Direction :", latest.direction)
    print("Event     :", latest.event)
    print("Price     :", round(latest.price, 2))
