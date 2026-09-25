from dataclasses import dataclass
from typing import List, Optional

from models.candle import Candle
from detectors.institutional_order_block_detector import (
    InstitutionalOrderBlock,
    InstitutionalOrderBlockDetector,
)


@dataclass
class BreakerBlock:
    index: int
    time: object

    direction: str
    high: float
    low: float

    strength: float

    origin_ob_index: int
    origin_ob_time: object

    invalidation_index: int
    invalidation_time: object

    retested: bool = False
    retest_index: int = -1
    retest_time: object = None

    confirmed: bool = False
    confirmation_index: int = -1
    confirmation_time: object = None


class BreakerBlockDetector:

    def __init__(
        self,
        retest_tolerance: float = 0.15,
        confirmation_candles: int = 3,
        min_strength: float = 1.0,
    ):
        self.retest_tolerance = retest_tolerance
        self.confirmation_candles = confirmation_candles
        self.min_strength = min_strength

        self.ob_detector = InstitutionalOrderBlockDetector()

    # =========================================================
    # MAIN DETECTOR
    # =========================================================

    def detect(
        self,
        candles: List[Candle],
        order_blocks: Optional[
            List[InstitutionalOrderBlock]
        ] = None,
    ) -> List[BreakerBlock]:

        if len(candles) < 10:
            return []

        if order_blocks is None:
            order_blocks = self.ob_detector.process(candles)

        breakers = []

        for ob in order_blocks:

            if ob.strength < self.min_strength:
                continue

            # A breaker must come from an invalidated OB.
            if not ob.invalidated:
                continue

            if ob.invalidation_index < 0:
                continue

            breaker = self._create_breaker(
                ob,
                candles,
            )

            if breaker is None:
                continue

            self._detect_retest(
                breaker,
                candles,
            )

            self._detect_confirmation(
                breaker,
                candles,
            )

            breakers.append(breaker)

        breakers = self.remove_duplicates(breakers)

        breakers.sort(
            key=lambda x: x.invalidation_index
        )

        return breakers

    # =========================================================
    # CREATE BREAKER
    # =========================================================

    def _create_breaker(
        self,
        ob: InstitutionalOrderBlock,
        candles: List[Candle],
    ) -> Optional[BreakerBlock]:

        invalidation_index = ob.invalidation_index

        if invalidation_index >= len(candles):
            return None

        # -----------------------------------------------------
        # Bullish OB broken downward
        #
        # Bullish OB
        #       ↓
        # price breaks LOW
        #       ↓
        # becomes Bearish Breaker
        # -----------------------------------------------------

        if ob.direction == "BULLISH":

            direction = "BEARISH"

        # -----------------------------------------------------
        # Bearish OB broken upward
        #
        # Bearish OB
        #       ↓
        # price breaks HIGH
        #       ↓
        # becomes Bullish Breaker
        # -----------------------------------------------------

        else:

            direction = "BULLISH"

        return BreakerBlock(
            index=invalidation_index,
            time=candles[invalidation_index].time,

            direction=direction,

            high=ob.high,
            low=ob.low,

            strength=ob.strength,

            origin_ob_index=ob.index,
            origin_ob_time=ob.time,

            invalidation_index=invalidation_index,
            invalidation_time=candles[
                invalidation_index
            ].time,
        )

    # =========================================================
    # RETEST DETECTION
    # =========================================================

    def _detect_retest(
        self,
        breaker: BreakerBlock,
        candles: List[Candle],
    ) -> None:

        start = breaker.invalidation_index + 1

        if start >= len(candles):
            return

        for i in range(start, len(candles)):

            candle = candles[i]

            if self._price_touches_zone(
                candle,
                breaker,
            ):

                breaker.retested = True
                breaker.retest_index = i
                breaker.retest_time = candle.time

                return

    # =========================================================
    # CONFIRMATION
    # =========================================================

    def _detect_confirmation(
        self,
        breaker: BreakerBlock,
        candles: List[Candle],
    ) -> None:

        if not breaker.retested:
            return

        start = breaker.retest_index + 1

        end = min(
            len(candles),
            start + self.confirmation_candles,
        )

        for i in range(start, end):

            candle = candles[i]

            # -------------------------------------------------
            # Bearish breaker
            # Price should reject upward zone and close down.
            # -------------------------------------------------

            if breaker.direction == "BEARISH":

                if (
                    candle.close < candle.open
                    and candle.close < breaker.low
                ):

                    breaker.confirmed = True
                    breaker.confirmation_index = i
                    breaker.confirmation_time = candle.time

                    return

            # -------------------------------------------------
            # Bullish breaker
            # Price should reject downward zone and close up.
            # -------------------------------------------------

            else:

                if (
                    candle.close > candle.open
                    and candle.close > breaker.high
                ):

                    breaker.confirmed = True
                    breaker.confirmation_index = i
                    breaker.confirmation_time = candle.time

                    return

    # =========================================================
    # ZONE TOUCH
    # =========================================================

    def _price_touches_zone(
        self,
        candle: Candle,
        breaker: BreakerBlock,
    ) -> bool:

        zone_high = breaker.high
        zone_low = breaker.low

        tolerance = self.retest_tolerance

        # Extend the zone slightly to account for spread/
        # small overshoots during a retest.

        expanded_high = zone_high + tolerance
        expanded_low = zone_low - tolerance

        return (
            candle.low <= expanded_high
            and candle.high >= expanded_low
        )

    # =========================================================
    # VALID BREAKERS
    # =========================================================

    def get_valid(
        self,
        breakers: List[BreakerBlock],
    ) -> List[BreakerBlock]:

        return [
            breaker
            for breaker in breakers
            if breaker.confirmed
        ]

    # =========================================================
    # RETESTED BREAKERS
    # =========================================================

    def get_retested(
        self,
        breakers: List[BreakerBlock],
    ) -> List[BreakerBlock]:

        return [
            breaker
            for breaker in breakers
            if breaker.retested
        ]

    # =========================================================
    # UNCONFIRMED BREAKERS
    # =========================================================

    def get_unconfirmed(
        self,
        breakers: List[BreakerBlock],
    ) -> List[BreakerBlock]:

        return [
            breaker
            for breaker in breakers
            if not breaker.confirmed
        ]

    # =========================================================
    # BULLISH BREAKERS
    # =========================================================

    def get_bullish(
        self,
        breakers: List[BreakerBlock],
    ) -> List[BreakerBlock]:

        return [
            breaker
            for breaker in breakers
            if breaker.direction == "BULLISH"
        ]

    # =========================================================
    # BEARISH BREAKERS
    # =========================================================

    def get_bearish(
        self,
        breakers: List[BreakerBlock],
    ) -> List[BreakerBlock]:

        return [
            breaker
            for breaker in breakers
            if breaker.direction == "BEARISH"
        ]

    # =========================================================
    # DUPLICATE REMOVAL
    # =========================================================

    def remove_duplicates(
        self,
        breakers: List[BreakerBlock],
        tolerance: float = 0.50,
    ) -> List[BreakerBlock]:

        filtered = []

        # Strongest first.
        ordered = sorted(
            breakers,
            key=lambda x: x.strength,
            reverse=True,
        )

        for breaker in ordered:

            duplicate = False

            for existing in filtered:

                if (
                    existing.direction
                    != breaker.direction
                ):
                    continue

                high_close = (
                    abs(
                        existing.high
                        - breaker.high
                    )
                    <= tolerance
                )

                low_close = (
                    abs(
                        existing.low
                        - breaker.low
                    )
                    <= tolerance
                )

                if high_close and low_close:
                    duplicate = True
                    break

            if not duplicate:
                filtered.append(breaker)

        filtered.sort(
            key=lambda x: x.invalidation_index
        )

        return filtered

    # =========================================================
    # PROCESS
    # =========================================================

    def process(
        self,
        candles: List[Candle],
    ) -> List[BreakerBlock]:

        order_blocks = self.ob_detector.process(
            candles
        )

        return self.detect(
            candles,
            order_blocks,
        )
