from dataclasses import dataclass
from typing import List

from models.candle import Candle
from detectors.displacement_detector import DisplacementDetector
from detectors.internal_structure_detector import InternalStructureDetector
from detectors.liquidity_grab_detector import LiquidityGrabDetector


@dataclass
class InstitutionalOrderBlock:

    index: int
    time: object

    direction: str

    high: float
    low: float

    strength: float

    mitigated: bool = False

    invalidated: bool = False
    invalidation_index: int = -1
    invalidation_time: object = None

    liquidity_time: object = None
    structure_time: object = None
    displacement_time: object = None


class InstitutionalOrderBlockDetector:

    def __init__(self):

        self.displacement = DisplacementDetector()
        self.structure = InternalStructureDetector()
        self.liquidity = LiquidityGrabDetector()

    # =========================================================
    # DETECT INSTITUTIONAL ORDER BLOCKS
    # =========================================================

    def detect(
        self,
        candles: List[Candle],
    ) -> List[InstitutionalOrderBlock]:

        order_blocks = []

        if len(candles) < 20:
            return order_blocks

        displacement_events = self.displacement.detect(
            candles
        )

        structure_events = self.structure.detect(
            candles
        )

        liquidity_events = self.liquidity.detect(
            candles
        )

        if not displacement_events:
            return []

        if not structure_events:
            return []

        if not liquidity_events:
            return []

        for displacement in displacement_events:

            direction = displacement.direction

            # -------------------------------------------------
            # Find confirmed liquidity grab before displacement
            # -------------------------------------------------

            liquidity = None

            for grab in reversed(liquidity_events):

                if grab.time >= displacement.time:
                    continue

                if direction == "BULLISH":

                    if (
                        grab.direction == "BULLISH"
                        and grab.confirmed
                    ):
                        liquidity = grab
                        break

                else:

                    if (
                        grab.direction == "BEARISH"
                        and grab.confirmed
                    ):
                        liquidity = grab
                        break

            if liquidity is None:
                continue

            # -------------------------------------------------
            # Find same-direction structure after displacement
            # -------------------------------------------------

            structure = None

            for event in structure_events:

                if event.time <= displacement.time:
                    continue

                if event.direction != direction:
                    continue

                structure = event
                break

            if structure is None:
                continue

            # -------------------------------------------------
            # Find last opposite candle
            # -------------------------------------------------

            ob_candle = None
            ob_index = None

            start = max(
                0,
                displacement.index - 6,
            )

            for i in range(
                displacement.index - 1,
                start - 1,
                -1,
            ):

                candle = candles[i]

                # Bullish displacement:
                # last bearish candle becomes bullish OB.

                if direction == "BULLISH":

                    if candle.close < candle.open:

                        ob_candle = candle
                        ob_index = i
                        break

                # Bearish displacement:
                # last bullish candle becomes bearish OB.

                else:

                    if candle.close > candle.open:

                        ob_candle = candle
                        ob_index = i
                        break

            if ob_candle is None:
                continue

            if ob_index is None:
                continue

            strength = displacement.strength

            order_blocks.append(
                InstitutionalOrderBlock(

                    index=ob_index,

                    time=ob_candle.time,

                    direction=direction,

                    high=ob_candle.high,

                    low=ob_candle.low,

                    strength=round(
                        strength,
                        2,
                    ),

                    liquidity_time=liquidity.time,

                    structure_time=structure.time,

                    displacement_time=displacement.time,
                )
            )

        order_blocks = self.remove_duplicates(
            order_blocks
        )

        return order_blocks

    # =========================================================
    # REMOVE DUPLICATES
    # =========================================================

    def remove_duplicates(
        self,
        order_blocks: List[InstitutionalOrderBlock],
        tolerance: float = 0.50,
    ) -> List[InstitutionalOrderBlock]:

        filtered = []

        ordered = sorted(
            order_blocks,
            key=lambda x: x.strength,
            reverse=True,
        )

        for ob in ordered:

            duplicate = False

            for existing in filtered:

                if existing.direction != ob.direction:
                    continue

                high_close = (
                    abs(
                        existing.high - ob.high
                    ) <= tolerance
                )

                low_close = (
                    abs(
                        existing.low - ob.low
                    ) <= tolerance
                )

                if high_close and low_close:

                    duplicate = True
                    break

            if not duplicate:
                filtered.append(ob)

        filtered.sort(
            key=lambda x: x.index
        )

        return filtered

    # =========================================================
    # MARK MITIGATION + INVALIDATION
    # =========================================================

    def mark_mitigated(
        self,
        order_blocks: List[InstitutionalOrderBlock],
        candles: List[Candle],
    ) -> List[InstitutionalOrderBlock]:

        for ob in order_blocks:

            # Reset state so process() remains deterministic.

            ob.mitigated = False
            ob.invalidated = False
            ob.invalidation_index = -1
            ob.invalidation_time = None

            start = ob.index + 1

            for i in range(
                start,
                len(candles),
            ):

                candle = candles[i]

                # =================================================
                # BULLISH ORDER BLOCK
                # =================================================

                if ob.direction == "BULLISH":

                    # Price has entered/touched the OB.

                    if (
                        candle.low <= ob.high
                        and candle.high >= ob.low
                    ):

                        ob.mitigated = True

                    # Full bearish invalidation.
                    #
                    # Close below the entire OB means the
                    # bullish institutional zone has failed.

                    if candle.close < ob.low:

                        ob.invalidated = True
                        ob.invalidation_index = i
                        ob.invalidation_time = candle.time

                        break

                # =================================================
                # BEARISH ORDER BLOCK
                # =================================================

                else:

                    # Price has entered/touched the OB.

                    if (
                        candle.high >= ob.low
                        and candle.low <= ob.high
                    ):

                        ob.mitigated = True

                    # Full bullish invalidation.
                    #
                    # Close above the entire OB means the
                    # bearish institutional zone has failed.

                    if candle.close > ob.high:

                        ob.invalidated = True
                        ob.invalidation_index = i
                        ob.invalidation_time = candle.time

                        break

        return order_blocks

    # =========================================================
    # UNMITIGATED
    # =========================================================

    def get_unmitigated(
        self,
        order_blocks: List[InstitutionalOrderBlock],
    ) -> List[InstitutionalOrderBlock]:

        return [
            ob
            for ob in order_blocks
            if not ob.mitigated
        ]

    # =========================================================
    # INVALIDATED
    # =========================================================

    def get_invalidated(
        self,
        order_blocks: List[InstitutionalOrderBlock],
    ) -> List[InstitutionalOrderBlock]:

        return [
            ob
            for ob in order_blocks
            if ob.invalidated
        ]

    # =========================================================
    # VALID / ACTIVE
    # =========================================================

    def get_active(
        self,
        order_blocks: List[InstitutionalOrderBlock],
    ) -> List[InstitutionalOrderBlock]:

        return [
            ob
            for ob in order_blocks
            if not ob.invalidated
        ]

    # =========================================================
    # BULLISH
    # =========================================================

    def get_bullish(
        self,
        order_blocks: List[InstitutionalOrderBlock],
    ) -> List[InstitutionalOrderBlock]:

        return [
            ob
            for ob in order_blocks
            if ob.direction == "BULLISH"
        ]

    # =========================================================
    # BEARISH
    # =========================================================

    def get_bearish(
        self,
        order_blocks: List[InstitutionalOrderBlock],
    ) -> List[InstitutionalOrderBlock]:

        return [
            ob
            for ob in order_blocks
            if ob.direction == "BEARISH"
        ]

    # =========================================================
    # PROCESS
    # =========================================================

    def process(
        self,
        candles: List[Candle],
    ) -> List[InstitutionalOrderBlock]:

        order_blocks = self.detect(
            candles
        )

        order_blocks = self.mark_mitigated(
            order_blocks,
            candles,
        )

        return order_blocks
