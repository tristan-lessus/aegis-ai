from feeds.provider_factory import ProviderFactory
from detectors.fvg_detector import FVGDetector

provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300,
)

detector = FVGDetector(min_size=0.30)

gaps = detector.detect(candles)

print("=" * 60)
print("FAIR VALUE GAPS")
print("=" * 60)

for gap in gaps:
    print(
        f"{gap.time} | "
        f"{gap.direction:<8} | "
        f"{gap.bottom:.2f} -> {gap.top:.2f} | "
        f"Size={gap.size}"
    )

print()
print("Total FVGs:", len(gaps))

print()
print("=" * 60)
print("LATEST FVG")
print("=" * 60)

if gaps:
    latest = gaps[-1]
    print(latest)
else:
    print("No FVG detected.")
