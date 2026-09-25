from dataclasses import dataclass
from typing import List, Optional

from detectors.swing_detector import SwingPoint


@dataclass
class LiquidityZone:
    type: str
    price: float
    first_index: int
    second_index: int

    swept: bool = False

    # Direction created by the sweep.
    # SSL sweep -> BULLISH
    # BSL sweep -> BEARISH
    direction: str = "NONE"

    # Candle where the sweep happened.
    sweep_index: Optional[int] = None
    sweep_time: object = None

    # Confirmation candle index/time.
    confirmation_index: Optional[int] = None
    confirmation_time: object = None

    # Strength of the sweep.
    sweep_strength: float = 0.0


class LiquidityDetector:

    def __init__(
        self,
        tolerance=0.0005,
        max_swing_distance=8,
        confirmation_candles=3,
    ):
        self.tolerance = tolerance
        self.max_swing_distance = max_swing_distance
        self.confirmation_candles = confirmation_candles

    # ==========================================================
    # LIQUIDITY POOLS
    # ==========================================================

    def detect(
        self,
        swings: List[SwingPoint],
    ) -> List[LiquidityZone]:

        zones = []

        if len(swings) < 2:
            return zones

        for i in range(len(swings)):

            for j in range(
                i + 1,
                min(
                    i + 1 + self.max_swing_distance,
                    len(swings),
                ),
            ):

                first = swings[i]
                second = swings[j]

                # Only compare equal swing types.
                if first.type != second.type:
                    continue

                average = (
                    first.price + second.price
                ) / 2.0

                if average <= 0:
                    continue

                difference = abs(
                    first.price - second.price
                )

                relative_difference = (
                    difference / average
                )

                if (
                    relative_difference
                    > self.tolerance
                ):
                    continue

                if first.type == "HIGH":

                    zone_type = "BSL"

                else:

                    zone_type = "SSL"

                zones.append(
                    LiquidityZone(
                        type=zone_type,
                        price=round(
                            average,
                            5,
                        ),
                        first_index=first.index,
                        second_index=second.index,
                    )
                )

        return self._remove_duplicate_zones(
            zones
        )

    # ==========================================================
    # SWEEP DETECTION
    # ==========================================================

    def detect_sweeps(
        self,
        zones: List[LiquidityZone],
        candles,
    ):

        if not zones or not candles:
            return zones

        for zone in zones:

            start_index = max(
                0,
                zone.second_index + 1,
            )

            for i in range(
                start_index,
                len(candles),
            ):

                candle = candles[i]

                # --------------------------------------------------
                # BUY-SIDE LIQUIDITY
                #
                # Price trades ABOVE the equal highs,
                # then closes back BELOW the liquidity.
                #
                # This is bearish liquidity-taking behaviour.
                # --------------------------------------------------

                if zone.type == "BSL":

                    swept_above = (
                        candle.high
                        > zone.price
                    )

                    rejected = (
                        candle.close
                        < zone.price
                    )

                    if swept_above and rejected:

                        penetration = (
                            candle.high
                            - zone.price
                        )

                        zone.swept = True
                        zone.direction = "BEARISH"
                        zone.sweep_index = i
                        zone.sweep_time = (
                            candle.time
                        )

                        zone.sweep_strength = round(
                            penetration,
                            5,
                        )

                        confirmation = (
                            self._find_confirmation(
                                candles,
                                i,
                                "BEARISH",
                                zone.price,
                            )
                        )

                        if confirmation:

                            (
                                confirmation_index,
                                confirmation_candle,
                            ) = confirmation

                            zone.confirmation_index = (
                                confirmation_index
                            )

                            zone.confirmation_time = (
                                confirmation_candle.time
                            )

                        break

                # --------------------------------------------------
                # SELL-SIDE LIQUIDITY
                #
                # Price trades BELOW equal lows,
                # then closes back ABOVE the liquidity.
                #
                # This is bullish liquidity-taking behaviour.
                # --------------------------------------------------

                else:

                    swept_below = (
                        candle.low
                        < zone.price
                    )

                    rejected = (
                        candle.close
                        > zone.price
                    )

                    if swept_below and rejected:

                        penetration = (
                            zone.price
                            - candle.low
                        )

                        zone.swept = True
                        zone.direction = "BULLISH"
                        zone.sweep_index = i
                        zone.sweep_time = (
                            candle.time
                        )

                        zone.sweep_strength = round(
                            penetration,
                            5,
                        )

                        confirmation = (
                            self._find_confirmation(
                                candles,
                                i,
                                "BULLISH",
                                zone.price,
                            )
                        )

                        if confirmation:

                            (
                                confirmation_index,
                                confirmation_candle,
                            ) = confirmation

                            zone.confirmation_index = (
                                confirmation_index
                            )

                            zone.confirmation_time = (
                                confirmation_candle.time
                            )

                        break

        return zones

    # ==========================================================
    # CONFIRMATION
    # ==========================================================

    def _find_confirmation(
        self,
        candles,
        sweep_index,
        direction,
        liquidity_price,
    ):

        end_index = min(
            len(candles),
            sweep_index
            + 1
            + self.confirmation_candles,
        )

        for i in range(
            sweep_index + 1,
            end_index,
        ):

            candle = candles[i]

            if direction == "BULLISH":

                # Confirmation must hold above the
                # swept SSL level.

                if candle.close > liquidity_price:

                    return i, candle

            else:

                # Confirmation must hold below the
                # swept BSL level.

                if candle.close < liquidity_price:

                    return i, candle

        return None

    # ==========================================================
    # DUPLICATE CLEANUP
    # ==========================================================

    def _remove_duplicate_zones(
        self,
        zones: List[LiquidityZone],
    ) -> List[LiquidityZone]:

        if not zones:
            return []

        result = []

        for zone in zones:

            duplicate = False

            for existing in result:

                if (
                    existing.type
                    != zone.type
                ):
                    continue

                average = (
                    existing.price
                    + zone.price
                ) / 2.0

                if average == 0:
                    continue

                difference = abs(
                    existing.price
                    - zone.price
                )

                if (
                    difference / average
                    <= self.tolerance
                ):

                    duplicate = True
                    break

            if not duplicate:

                result.append(zone)

        return result

    # ==========================================================
    # ACTIVE LIQUIDITY
    # ==========================================================

    def get_swept_liquidity(
        self,
        zones: List[LiquidityZone],
        direction: Optional[str] = None,
    ) -> List[LiquidityZone]:

        swept = [
            zone
            for zone in zones
            if zone.swept
        ]

        if direction is None:
            return swept

        return [
            zone
            for zone in swept
            if zone.direction == direction
        ]

    # ==========================================================
    # MOST RECENT SWEEP
    # ==========================================================

    def get_latest_sweep(
        self,
        zones: List[LiquidityZone],
        direction: Optional[str] = None,
    ):

        candidates = self.get_swept_liquidity(
            zones,
            direction,
        )

        if not candidates:
            return None

        candidates.sort(
            key=lambda zone: (
                zone.sweep_index
                if zone.sweep_index is not None
                else -1
            )
        )

        return candidates[-1]
