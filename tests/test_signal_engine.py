from engine.signal_engine import SignalEngine
from engine.confluence_engine import TradeSetup

signal = SignalEngine()

setup = signal.generate(
    structure_events=[TradeSetup("BULLISH", 0, [])],
    liquidity_events=[1],
    displacement_events=[1],
    fvg_events=[1],
    mitigation_events=[1],
    zone="DISCOUNT",
)

print("=" * 60)
print("AEGIS AI SIGNAL")
print("=" * 60)

print("Direction :", setup.direction)
print("Confidence:", f"{setup.confidence}%")

print("\nReasons:")

for reason in setup.reasons:
    print(f"✓ {reason}")
