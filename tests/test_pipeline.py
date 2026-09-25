from feeds.provider_factory import ProviderFactory
from engine.analysis_pipeline import AnalysisPipeline


provider = ProviderFactory.create("live")

candles = provider.get_candles(
    "XAU/USD",
    "M5",
    300,
)

pipeline = AnalysisPipeline()
signal = pipeline.analyze(candles)

print("=" * 60)
print("AEGIS AI")
print("=" * 60)

print("Current Price :", signal.current_price)
print("Latest Candle :", candles[-1].time)

print()
print("Direction     :", signal.direction)
print("Confidence    :", f"{signal.confidence}%")

print("\nReasons")
for reason in signal.reasons:
    print(f"✓ {reason}")

print()
print("=" * 60)
print("TRADE SETUP")
print("=" * 60)

print("Entry      :", signal.entry)
print("Stop Loss  :", signal.stop_loss)
print("TP1        :", signal.take_profit_1)
print("TP2        :", signal.take_profit_2)
print("RR         :", signal.risk_reward)
print("Entry Zone :", signal.entry_zone)
print("Setup Type :", signal.setup_type)
print("Status     :", signal.setup_status)
print("Valid      :", signal.trade_valid)

if signal.validation_reasons:
    print("\nValidation")
    for reason in signal.validation_reasons:
        print("!", reason)

if getattr(signal, "reason", None):
    print("\nReason     :", signal.reason)

if signal.entry_source_time:
    print("Source     :", signal.entry_source_time)

print()
print("=" * 60)
print("ENTRY CANDIDATES")
print("=" * 60)

current_index = len(candles) - 1


def show_zone(name, zone):
    if zone is None:
        return

    index = getattr(
        zone,
        "index",
        getattr(zone, "start_index", None),
    )

    if index is None:
        index = getattr(
            zone,
            "confirmation_index",
            getattr(zone, "retest_index", None),
        )

    try:
        index = int(index)
        age = current_index - index
    except (TypeError, ValueError):
        age = "UNKNOWN"

    direction = getattr(
        zone,
        "direction",
        "UNKNOWN",
    )

    time = getattr(
        zone,
        "time",
        getattr(zone, "start_time", None),
    )

    if time is None:
        time = getattr(
            zone,
            "confirmation_time",
            getattr(zone, "retest_time", None),
        )

    low = getattr(
        zone,
        "low",
        getattr(zone, "bottom", None),
    )

    high = getattr(
        zone,
        "high",
        getattr(zone, "top", None),
    )

    print()
    print(name)
    print("  Direction :", direction)
    print("  Index     :", index)
    print("  Age       :", age, "bars")
    print("  Time      :", time)
    print("  Low       :", low)
    print("  High      :", high)


print("\nFVGs")
for fvg in signal.fvg_events:
    show_zone("FVG", fvg)

print("\nBreaker Blocks")
for breaker in signal.breaker_blocks:
    show_zone("BREAKER", breaker)

print("\nOrder Blocks")
for ob in signal.order_blocks:
    show_zone("ORDER BLOCK", ob)

print()
print("=" * 60)
print("SUPPORT / RESISTANCE")
print("=" * 60)

for level in signal.support_resistance:
    print(
        f"{level.level_type:<12} "
        f"{level.price:<10.2f} "
        f"strength={level.strength:<5} "
        f"touches={level.touches:<2} "
        f"last_index={level.last_index}"
    )
