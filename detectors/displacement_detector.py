from dataclasses import dataclass
from statistics import mean
from typing import List

from models.candle import Candle


@dataclass
class Displacement:
    index: int
    time: object
    direction: str
    body: float
    strength: float


class DisplacementDetector:

    def __init__(self, lookback: int = 20, multiplier: float = 3.0):
        self.lookback = lookback
        self.multiplier = multiplier

    def detect(self, candles: List[Candle]) -> List[Displacement]:

        if len(candles) < self.lookback:
            return []

        events = []

        for i in range(self.lookback, len(candles)):

            history = candles[i - self.lookback:i]

            avg_body = mean(
                abs(c.close - c.open)
                for c in history
            )

            candle = candles[i]

            body = abs(candle.close - candle.open)

            if body < avg_body * self.multiplier:
                continue

            upper_wick = candle.high - max(candle.open, candle.close)
            lower_wick = min(candle.open, candle.close) - candle.low

            # Ignore candles with large wicks
            if upper_wick > body * 0.35:
                continue

            if lower_wick > body * 0.35:
                continue

            direction = (
                "BULLISH"
                if candle.close > candle.open
                else "BEARISH"
            )

            events.append(
                Displacement(
                    index=i,
                    time=candle.time,
                    direction=direction,
                    body=round(body, 2),
                    strength=round(body / avg_body, 2)
                )
            )

        return events

    def has_displacement(
        self,
        candles: List[Candle],
        start_index: int,
        end_index: int,
        direction: str,
    ) -> bool:
        """
        Returns True if a displacement candle exists between
        start_index and end_index in the given direction.
        """

        events = self.detect(candles)

        for event in events:

            if event.index < start_index:
                continue

            if event.index > end_index:
                continue

            if event.direction != direction.upper():
                continue

            return True

        return False
