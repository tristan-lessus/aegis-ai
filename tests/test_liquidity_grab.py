from feeds.provider_factory import ProviderFactory
from detectors.liquidity_grab_detector import LiquidityGrabDetector


provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300
)

detector = LiquidityGrabDetector()

events = detector.detect(candles)

print("=" * 60)
print("LIQUIDITY GRABS")
print("=" * 60)

if not events:
    print("No Liquidity Grabs Found")

for event in events:

    print(
        f"{event.time} | "
        f"{event.direction:<8} | "
        f"{event.liquidity:<3} | "
        f"Level={event.level:.2f} | "
        f"Sweep={event.sweep_price:.2f} | "
        f"Confirmed={event.confirmed}"
    )

print()
print("Total Events:", len(events))

if events:

    latest = events[-1]

    print()
    print("=" * 60)
    print("LATEST LIQUIDITY GRAB")
    print("=" * 60)
    print("Time       :", latest.time)
    print("Direction  :", latest.direction)
    print("Liquidity  :", latest.liquidity)
    print("Level      :", round(latest.level, 2))
    print("Sweep      :", round(latest.sweep_price, 2))
    print("Confirmed  :", latest.confirmed)
