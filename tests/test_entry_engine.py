from feeds.provider_factory import ProviderFactory

from engine.entry_engine import EntryEngine
from detectors.swing_detector import SwingDetector

provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300
)

# Current market price
current_price = candles[-1].close

# Detect swings
detector = SwingDetector()

swings = detector.detect(candles)

# Latest swing high
swing_high = max(
    s.price
    for s in swings
    if s.type == "HIGH"
)

# Latest swing low
swing_low = min(
    s.price
    for s in swings
    if s.type == "LOW"
)

engine = EntryEngine()

setup = engine.generate(
    direction="BULLISH",
    current_price=current_price,
    swing_high=swing_high,
    swing_low=swing_low,
)

print("=" * 60)
print("LIVE ENTRY ENGINE")
print("=" * 60)

print("Current Price :", round(current_price, 2))
print("Swing High    :", round(swing_high, 2))
print("Swing Low     :", round(swing_low, 2))
print()

print("Direction :", setup.direction)
print("Entry     :", setup.entry)
print("SL        :", setup.stop_loss)
print("TP1       :", setup.take_profit_1)
print("TP2       :", setup.take_profit_2)
print("RR        :", setup.risk_reward)
