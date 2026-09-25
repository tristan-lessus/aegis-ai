from feeds.provider_factory import ProviderFactory

from detectors.swing_detector import SwingDetector
from detectors.structure_classifier import StructureClassifier
from detectors.premium_discount_detector import PremiumDiscountDetector


provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300,
)

swings = SwingDetector().detect(candles)

classified = StructureClassifier().classify(swings)

current_price = candles[-1].close

zone = PremiumDiscountDetector().detect(
    classified,
    current_price,
)

print("=" * 60)
print("PREMIUM / DISCOUNT")
print("=" * 60)

print(f"Swing High : {zone.high}")
print(f"Swing Low  : {zone.low}")
print(f"EQ         : {zone.equilibrium}")
print(f"Price      : {zone.current_price}")
print(f"Zone       : {zone.zone}")
