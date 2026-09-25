from feeds.provider_factory import ProviderFactory

from detectors.fvg_detector import FVGDetector
from detectors.mitigation_detector import MitigationDetector


provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300,
)

fvgs = FVGDetector().detect(candles)

mitigations = MitigationDetector().detect(
    candles,
    fvgs,
)

print("=" * 60)
print("MITIGATIONS")
print("=" * 60)

for m in mitigations:
    print(
        f"{m.time} | "
        f"{m.direction:<8} | "
        f"{m.zone_type:<15} | "
        f"{m.bottom:.2f} -> {m.top:.2f}"
    )

print("\nTotal:", len(mitigations))
