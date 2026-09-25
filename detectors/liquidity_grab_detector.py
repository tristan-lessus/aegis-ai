from dataclasses import dataclass
from typing import List

from models.candle import Candle
from detectors.swing_detector import SwingDetector


@dataclass
class LiquidityGrab:
    index: int
    time: object
    direction: str          # BULLISH / BEARISH
    liquidity: str          # BSL / SSL
    level: float
    sweep_price: float
    confirmed: bool


class LiquidityGrabDetector:

    def __init__(
        self,
        tolerance: float = 0.001,
        confirmation_candles: int = 3
    ):
        self.tolerance = tolerance
        self.confirmation_candles = confirmation_candles
        self.swing_detector = SwingDetector()

    def detect(self, candles: List[Candle]) -> List[LiquidityGrab]:

        if len(candles) < 20:
            return []

        swings = self.swing_detector.detect(candles)

        grabs = []

        # -----------------------------------------
        # Compare nearby swing points
        # -----------------------------------------

        for i in range(len(swings)):

            for j in range(i + 1, min(i + 8, len(swings))):

                s1 = swings[i]
                s2 = swings[j]

                if s1.type != s2.type:
                    continue

                average = (s1.price + s2.price) / 2

                if abs(s1.price - s2.price) / average > self.tolerance:
                    continue

                # ---------------------------------
                # BUY SIDE LIQUIDITY
                # ---------------------------------

                if s1.type == "HIGH":

                    for k in range(s2.index + 1, len(candles)):

                        candle = candles[k]

                        if candle.high <= average:
                            continue

                        confirmed = False

                        end = min(
                            len(candles),
                            k + self.confirmation_candles + 1
                        )

                        for future in candles[k + 1:end]:

                            if future.close < average:
                                confirmed = True
                                break

                        grabs.append(
                            LiquidityGrab(
                                index=k,
                                time=candle.time,
                                direction="BEARISH",
                                liquidity="BSL",
                                level=round(average, 2),
                                sweep_price=round(candle.high, 2),
                                confirmed=confirmed
                            )
                        )

                        break

                # ---------------------------------
                # SELL SIDE LIQUIDITY
                # ---------------------------------

                else:

                    for k in range(s2.index + 1, len(candles)):

                        candle = candles[k]

                        if candle.low >= average:
                            continue

                        confirmed = False

                        end = min(
                            len(candles),
                            k + self.confirmation_candles + 1
                        )

                        for future in candles[k + 1:end]:

                            if future.close > average:
                                confirmed = True
                                break

                        grabs.append(
                            LiquidityGrab(
                                index=k,
                                time=candle.time,
                                direction="BULLISH",
                                liquidity="SSL",
                                level=round(average, 2),
                                sweep_price=round(candle.low, 2),
                                confirmed=confirmed
                            )
                        )

                        break

        # -----------------------------------------
        # Remove duplicates
        # -----------------------------------------

        unique = []

        seen = set()

        for event in grabs:

            key = (
                event.time,
                event.direction,
                event.liquidity
            )

            if key in seen:
                continue

            seen.add(key)

            unique.append(event)

        return unique
