from dataclasses import dataclass


@dataclass
class SwingPoint:
    index: int
    time: object
    price: float
    type: str  # HIGH / LOW


@dataclass
class StructureBreak:
    index: int
    time: object
    direction: str  # BULLISH / BEARISH
    type: str       # BOS / CHOCH
    level: float


class MarketStructureDetector:

    def __init__(self, lookback=3):
        self.lookback = lookback

    def detect_swings(self, candles):

        swings = []

        for i in range(self.lookback, len(candles) - self.lookback):

            high = candles[i].high
            low = candles[i].low

            swing_high = True
            swing_low = True

            for j in range(i - self.lookback, i + self.lookback + 1):

                if j == i:
                    continue

                if candles[j].high >= high:
                    swing_high = False

                if candles[j].low <= low:
                    swing_low = False

            if swing_high:
                swings.append(
                    SwingPoint(
                        index=i,
                        time=candles[i].time,
                        price=high,
                        type="HIGH",
                    )
                )

            if swing_low:
                swings.append(
                    SwingPoint(
                        index=i,
                        time=candles[i].time,
                        price=low,
                        type="LOW",
                    )
                )

        swings.sort(key=lambda x: x.index)

        # Remove consecutive duplicate swing types,
        # keeping only the stronger one.
        filtered = []

        for swing in swings:

            if not filtered:
                filtered.append(swing)
                continue

            last = filtered[-1]

            if last.type == swing.type:

                if swing.type == "HIGH":

                    if swing.price > last.price:
                        filtered[-1] = swing

                else:

                    if swing.price < last.price:
                        filtered[-1] = swing

            else:
                filtered.append(swing)

        return filtered

    def detect_bos(self, candles, swings):

        breaks = []

        broken_swings = set()

        for swing in swings:

            for i in range(swing.index + 1, len(candles)):

                close = candles[i].close

                if swing.type == "HIGH":

                    if (
                        close > swing.price
                        and swing.index not in broken_swings
                    ):

                        breaks.append(
                            StructureBreak(
                                index=i,
                                time=candles[i].time,
                                direction="BULLISH",
                                type="BOS",
                                level=swing.price,
                            )
                        )

                        broken_swings.add(swing.index)
                        break

                else:

                    if (
                        close < swing.price
                        and swing.index not in broken_swings
                    ):

                        breaks.append(
                            StructureBreak(
                                index=i,
                                time=candles[i].time,
                                direction="BEARISH",
                                type="BOS",
                                level=swing.price,
                            )
                        )

                        broken_swings.add(swing.index)
                        break

        breaks.sort(key=lambda x: x.index)

        return breaks

    def process(self, candles):

        swings = self.detect_swings(candles)

        breaks = self.detect_bos(candles, swings)

        return swings, breaks
