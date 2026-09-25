from engine.trade_validator import TradeValidator


validator = TradeValidator(
    min_risk_reward=1.5
)


result = validator.validate(
    direction="BULLISH",
    entry=4429.44,
    stop_loss=4385.66,
    take_profit=4516.99,
    risk_reward=2.0,
)


print("=" * 60)
print("AEGIS AI TRADE VALIDATOR")
print("=" * 60)

print("Valid :", result.valid)

if result.valid:
    print("STATUS: TRADE APPROVED")
else:
    print("STATUS: TRADE REJECTED")

for reason in result.reasons:
    print("✓", reason)
