from dataclasses import dataclass
from typing import List

from models.candle import Candle


@dataclass
class FairValueGap:
    index: int
    time: object
    direction: str
    top: float
    bottom: float
    size: float

    mitigated: bool = False
    mitigation_index: int = -1
    mitigation_time: object = None

    active: bool = True


class FVGDetector:
    """
    Detects three-candle Fair Value Gaps.

    A detected FVG becomes inactive once price fully trades back
    through the zone after the FVG is created.

    This prevents AEGIS from repeatedly using an old/consumed
    FVG as a fresh entry zone.
    """

    def __init__(
        self,
        min_size: float = 0.30,
        max_active_zones: int = 12,
    ):
        self.min_size = float(min_size)
        self.max_active_zones = int(max_active_zones)

    def detect(
        self,
        candles: List[Candle],
    ) -> List[FairValueGap]:

        if len(candles) < 3:
            return []

        gaps = []

        for i in range(1, len(candles) - 1):

            left = candles[i - 1]
            middle = candles[i]
            right = candles[i + 1]

            # --------------------------------------------------
            # BULLISH FVG
            # --------------------------------------------------
            if left.high < right.low:

                gap = right.low - left.high

                if gap >= self.min_size:

                    fvg = FairValueGap(
                        index=i,
                        time=middle.time,
                        direction="BULLISH",
                        top=float(right.low),
                        bottom=float(left.high),
                        size=round(gap, 2),
                    )

                    gaps.append(fvg)

            # --------------------------------------------------
            # BEARISH FVG
            # --------------------------------------------------
            elif left.low > right.high:

                gap = left.low - right.high

                if gap >= self.min_size:

                    fvg = FairValueGap(
                        index=i,
                        time=middle.time,
                        direction="BEARISH",
                        top=float(left.low),
                        bottom=float(right.high),
                        size=round(gap, 2),
                    )

                    gaps.append(fvg)

        # Determine whether each FVG was subsequently mitigated.
        self._mark_mitigated(gaps, candles)

        # Keep only the most recent active FVGs plus recently
        # mitigated zones useful for diagnostics.
        gaps.sort(
            key=lambda zone: zone.index,
            reverse=True,
        )

        active = [
            zone
            for zone in gaps
            if zone.active
        ]

        inactive = [
            zone
            for zone in gaps
            if not zone.active
        ]

        active = active[
            : self.max_active_zones
        ]

        # Keep a smaller historical set so the dashboard/debugger
        # does not become overloaded with hundreds of old FVGs.
        inactive = inactive[:10]

        result = active + inactive

        result.sort(
            key=lambda zone: zone.index
        )

        return result

    def _mark_mitigated(
        self,
        gaps: List[FairValueGap],
        candles: List[Candle],
    ):
        """
        Mark an FVG inactive when a later candle trades through
        the entire gap.

        Bullish:
            price reaches the bottom of the gap.

        Bearish:
            price reaches the top of the gap.
        """

        if not gaps:
            return

        for gap in gaps:

            start = gap.index + 2

            if start >= len(candles):
                continue

            for i in range(
                start,
                len(candles),
            ):

                candle = candles[i]

                if gap.direction == "BULLISH":

                    # Price has traded back to / below the
                    # lower boundary of the bullish imbalance.
                    if candle.low <= gap.bottom:

                        gap.mitigated = True
                        gap.active = False
                        gap.mitigation_index = i
                        gap.mitigation_time = (
                            candle.time
                        )

                        break

                else:

                    # Price has traded back to / above the
                    # upper boundary of the bearish imbalance.
                    if candle.high >= gap.top:

                        gap.mitigated = True
                        gap.active = False
                        gap.mitigation_index = i
                        gap.mitigation_time = (
                            candle.time
                        )

                        break

    def active_gaps(
        self,
        gaps: List[FairValueGap],
        direction: str = None,
    ):

        result = [
            gap
            for gap in gaps
            if gap.active
            and not gap.mitigated
        ]

        if direction in (
            "BULLISH",
            "BEARISH",
        ):

            result = [
                gap
                for gap in result
                if gap.direction == direction
            ]

        return result
