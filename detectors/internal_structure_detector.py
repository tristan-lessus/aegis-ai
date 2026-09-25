from dataclasses import dataclass
from typing import List

from models.candle import Candle


@dataclass
class InternalStructure:
    index: int
    time: object
    direction: str
    event: str
    price: float


class InternalStructureDetector:

    def __init__(self, lookback: int = 2):
        self.lookback = lookback

    def detect(self, candles: List[Candle]) -> List[InternalStructure]:

        if len(candles) < self.lookback * 2 + 1:
            return []

        swings = []

        # -----------------------------
        # Detect Internal Swing Points
        # -----------------------------
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
                    {
                        "index": i,
                        "time": candles[i].time,
                        "price": high,
                        "type": "HIGH",
                    }
                )

            if swing_low:
                swings.append(
                    {
                        "index": i,
                        "time": candles[i].time,
                        "price": low,
                        "type": "LOW",
                    }
                )

        swings.sort(key=lambda x: x["index"])

        if len(swings) < 2:
            return []

        structures = []

        trend = None

        previous_high = None
        previous_low = None

        for swing in swings:

            if swing["type"] == "HIGH":

                if previous_high is None:
                    previous_high = swing
                    continue

                # Higher High
                if swing["price"] > previous_high["price"]:

                    if trend == "BEARISH":

                        structures.append(
                            InternalStructure(
                                index=swing["index"],
                                time=swing["time"],
                                direction="BULLISH",
                                event="CHOCH",
                                price=swing["price"],
                            )
                        )

                    else:

                        structures.append(
                            InternalStructure(
                                index=swing["index"],
                                time=swing["time"],
                                direction="BULLISH",
                                event="BOS",
                                price=swing["price"],
                            )
                        )

                    trend = "BULLISH"

                previous_high = swing

            else:

                if previous_low is None:
                    previous_low = swing
                    continue

                # Lower Low
                if swing["price"] < previous_low["price"]:

                    if trend == "BULLISH":

                        structures.append(
                            InternalStructure(
                                index=swing["index"],
                                time=swing["time"],
                                direction="BEARISH",
                                event="CHOCH",
                                price=swing["price"],
                            )
                        )

                    else:

                        structures.append(
                            InternalStructure(
                                index=swing["index"],
                                time=swing["time"],
                                direction="BEARISH",
                                event="BOS",
                                price=swing["price"],
                            )
                        )

                    trend = "BEARISH"

                previous_low = swing

        return structures
