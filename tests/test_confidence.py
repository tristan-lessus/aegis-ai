from engine.confidence_engine import ConfidenceEngine

engine = ConfidenceEngine()

result = engine.calculate(
    structure=True,
    liquidity=True,
    displacement=True,
    fvg=True,
    mitigation=True,
    premium_discount=True,
    order_block=False,
    session=False,
)

print("=" * 60)
print("CONFIDENCE ENGINE")
print("=" * 60)

print("Score :", result.score)

print("\nReasons")

for reason in result.reasons:
    print("✓", reason)
