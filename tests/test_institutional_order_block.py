from feeds.provider_factory import ProviderFactory
from detectors.institutional_order_block_detector import (
    InstitutionalOrderBlockDetector,
)

provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300,
)

detector = InstitutionalOrderBlockDetector()

order_blocks = detector.process(candles)

print("=" * 60)
print("INSTITUTIONAL ORDER BLOCKS")
print("=" * 60)

for ob in order_blocks:

    print(
        f"{ob.time} | "
        f"{ob.direction:<8} | "
        f"{ob.low:.2f} -> {ob.high:.2f} | "
        f"Strength={ob.strength:.2f} | "
        f"Mitigated={ob.mitigated}"
    )

print()
print("Total:", len(order_blocks))

if order_blocks:

    latest = order_blocks[-1]

    print()
    print("=" * 60)
    print("LATEST INSTITUTIONAL ORDER BLOCK")
    print("=" * 60)
    print("Time       :", latest.time)
    print("Direction  :", latest.direction)
    print("High       :", round(latest.high, 2))
    print("Low        :", round(latest.low, 2))
    print("Strength   :", latest.strength)
    print("Mitigated  :", latest.mitigated)
    print("Liquidity  :", latest.liquidity_time)
    print("Structure  :", latest.structure_time)
    print("Displacement :", latest.displacement_time)
