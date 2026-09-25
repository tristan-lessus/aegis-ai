from feeds.provider_factory import ProviderFactory

from detectors.breaker_block_detector import BreakerBlockDetector


provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300,
)

detector = BreakerBlockDetector()

breaker_blocks = detector.process(candles)

print("=" * 60)
print("BREAKER BLOCKS")
print("=" * 60)

for breaker in breaker_blocks:

    print(
        f"{breaker.time} | "
        f"{breaker.direction:<8} | "
        f"{breaker.low:.2f} -> {breaker.high:.2f} | "
        f"Strength={breaker.strength:.2f} | "
        f"Retested={breaker.retested} | "
        f"Confirmed={breaker.confirmed}"
    )

print()
print("Total:", len(breaker_blocks))

if breaker_blocks:

    latest = breaker_blocks[-1]

    print()
    print("=" * 60)
    print("LATEST BREAKER BLOCK")
    print("=" * 60)

    print("Time          :", latest.time)
    print("Direction     :", latest.direction)
    print("High          :", round(latest.high, 2))
    print("Low           :", round(latest.low, 2))
    print("Strength      :", latest.strength)
    print("Retested      :", latest.retested)
    print("Confirmed     :", latest.confirmed)
    print("Origin OB     :", latest.origin_ob_time)
    print("Invalidation  :", latest.invalidation_time)
    print("Retest Time   :", latest.retest_time)
    print("Confirmation  :", latest.confirmation_time)
