from telegram_alert import TelegramAlert


telegram = TelegramAlert()

message = """🤖 AEGIS AI — TEST ALERT

Symbol: XAU/USD
Timeframe: M5

Direction: 🔴 BEARISH
Setup: LIMIT
Status: VALID

Entry: 4350.04
Stop Loss: 4351.41
TP1: 4346.50
TP2: 4344.23

Risk/Reward: 2.57

MTF Status: CONFLICTING
Execution: MIXED_TIMEFRAME
Risk Mode: CAUTION
Confluence: 92%

Reasons:
• Bearish Structure
• Higher-Timeframe Conflict
• Liquidity Sweep
• Displacement
• Fair Value Gap
• Breaker Block

⚠️ TEST ALERT — NOT A LIVE TRADE
"""

if telegram.send(message):
    print("✅ Aegis Telegram alert delivered")
else:
    print("❌ Aegis Telegram alert failed")
