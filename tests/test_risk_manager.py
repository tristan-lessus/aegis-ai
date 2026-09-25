from risk.risk_manager import RiskManager


manager = RiskManager(
    risk_percent=1.0
)

result = manager.calculate(
    balance=100.0,
    entry=4429.44,
    stop_loss=4385.66,
)

print("=" * 60)
print("AEGIS AI RISK MANAGER")
print("=" * 60)

print("Balance       :", result.balance)
print("Risk %        :", result.risk_percent)
print("Risk Amount   :", result.risk_amount)
print("Entry         :", result.entry)
print("Stop Loss     :", result.stop_loss)
print("SL Distance   :", result.stop_distance)
print("Position Size :", result.position_size)
