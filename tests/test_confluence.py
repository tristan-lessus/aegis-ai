from engine.confluence_engine import ConfluenceEngine

engine = ConfluenceEngine()

setup = engine.evaluate(
    structure="BULLISH",
    liquidity=True,
    displacement=True,
    fvg=True,
    mitigation=True,
    premium_discount="DISCOUNT",
)

print("=" * 60)
print("CONFLUENCE ENGINE")
print("=" * 60)

print(f"Direction : {setup.direction}")
print(f"Confidence: {setup.confidence}%")

print("\nReasons:")

for reason in setup.reasons:
    print(f"✓ {reason}")
