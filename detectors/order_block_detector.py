from dataclasses import dataclass
from typing import List

from models.candle import Candle


@dataclass
class OrderBlock:
    index: int
    time: object
    direction: str
    high: float
    low: float
    mitigated: bool = False
    strength: float = 0.0


class OrderBlockDetector:

    def __init__(
        self,
        displacement_multiplier: float = 1.4,
        min_body: float = 1.5,
    ):
        self.displacement_multiplier = displacement_multiplier
        self.min_body = min_body

    def detect(self, candles: List[Candle]) -> List[OrderBlock]:

        order_blocks = []

        if len(candles) < 10:
            return order_blocks

        atr = self._calculate_atr(candles)

        for i in range(4, len(candles) - 3):

            current = candles[i]

            body = abs(current.close - current.open)

            # Ignore tiny candles
            if body < self.min_body:
                continue

            # Strong displacement
            if body < max(
                self.min_body,
                atr[i] * self.displacement_multiplier,
            ):
                continue

            # ======================================================
            # BULLISH ORDER BLOCK
            # ======================================================

            if current.close > current.open:

                previous = candles[i - 1]

                if previous.close < previous.open:

                    highs = [
                        candles[i - 1].high,
                        candles[i - 2].high,
                        candles[i - 3].high,
                    ]

                    if current.close > max(highs):

                        order_blocks.append(
                            OrderBlock(
                                index=i - 1,
                                time=previous.time,
                                direction="BULLISH",
                                high=previous.high,
                                low=previous.low,
                                strength=round(body / atr[i], 2),
                            )
                        )

            # ======================================================
            # BEARISH ORDER BLOCK
            # ======================================================

            else:

                previous = candles[i - 1]

                if previous.close > previous.open:

                    lows = [
                        candles[i - 1].low,
                        candles[i - 2].low,
                        candles[i - 3].low,
                    ]

                    if current.close < min(lows):

                        order_blocks.append(
                            OrderBlock(
                                index=i - 1,
                                time=previous.time,
                                direction="BEARISH",
                                high=previous.high,
                                low=previous.low,
                                strength=round(body / atr[i], 2),
                            )
                        )

        return order_blocks

    def _calculate_atr(
        self,
        candles: List[Candle],
        period: int = 14,
    ):

        true_ranges = []

        for i in range(len(candles)):

            if i == 0:
                tr = candles[i].high - candles[i].low
            else:
                tr = max(
                    candles[i].high - candles[i].low,
                    abs(candles[i].high - candles[i - 1].close),
                    abs(candles[i].low - candles[i - 1].close),
                )

            true_ranges.append(tr)

        atr = []

        for i in range(len(true_ranges)):

            if i < period:
                atr.append(sum(true_ranges[: i + 1]) / (i + 1))
            else:
                atr.append(
                    sum(true_ranges[i - period + 1 : i + 1]) / period
                )

        return atr

    def mark_mitigated(
        self,
        order_blocks: List[OrderBlock],
        candles: List[Candle],
    ) -> List[OrderBlock]:

        for ob in order_blocks:

            for candle in candles[ob.index + 1:]:

                if ob.direction == "BULLISH":

                    if (
                        candle.low <= ob.high
                        and candle.high >= ob.low
                    ):
                        ob.mitigated = True
                        break

                else:

                    if (
                        candle.high >= ob.low
                        and candle.low <= ob.high
                    ):
                        ob.mitigated = True
                        break

        return order_blocks

    def remove_duplicates(
        self,
        order_blocks: List[OrderBlock],
        tolerance: float = 0.50,
    ) -> List[OrderBlock]:

        filtered = []

        for ob in sorted(
            order_blocks,
            key=lambda x: x.strength,
            reverse=True,
        ):

            duplicate = False

            for existing in filtered:

                if (
                    existing.direction == ob.direction
                    and abs(existing.high - ob.high) <= tolerance
                    and abs(existing.low - ob.low) <= tolerance
                ):
                    duplicate = True
                    break

            if not duplicate:
                filtered.append(ob)

        filtered.sort(key=lambda x: x.index)

        return filtered

    def get_unmitigated(
        self,
        order_blocks: List[OrderBlock],
    ) -> List[OrderBlock]:

        return [
            ob
            for ob in order_blocks
            if not ob.mitigated
        ]

    def get_bullish(
        self,
        order_blocks: List[OrderBlock],
    ) -> List[OrderBlock]:

        return [
            ob
            for ob in order_blocks
            if ob.direction == "BULLISH"
        ]

    def get_bearish(
        self,
        order_blocks: List[OrderBlock],
    ) -> List[OrderBlock]:

        return [
            ob
            for ob in order_blocks
            if ob.direction == "BEARISH"
        ]

    def process(
        self,
        candles: List[Candle],
    ) -> List[OrderBlock]:

        order_blocks = self.detect(candles)
        order_blocks = self.remove_duplicates(order_blocks)
        order_blocks = self.mark_mitigated(order_blocks, candles)

        return order_blocks
