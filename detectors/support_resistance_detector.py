from dataclasses import dataclass
from typing import List

from models.candle import Candle
from detectors.swing_detector import SwingPoint


@dataclass
class SupportResistanceLevel:
    price: float
    level_type: str
    strength: float
    touches: int
    first_index: int
    last_index: int
    first_time: object
    last_time: object
    source: str = "SWING"


class SupportResistanceDetector:
    """
    Detects structural support and resistance.

    Important:
        Swing highs create resistance candidates.
        Swing lows create support candidates.

    The final target selection is always performed relative
    to the current market price.
    """

    def __init__(
        self,
        tolerance: float = 1.5,
        min_touches: int = 1,
        max_levels: int = 20,
        min_strength: float = 1.0,
    ):
        self.tolerance = float(tolerance)
        self.min_touches = int(min_touches)
        self.max_levels = int(max_levels)
        self.min_strength = float(min_strength)

    def detect(
        self,
        candles: List[Candle],
        swings: List[SwingPoint],
    ) -> List[SupportResistanceLevel]:

        if not candles or not swings:
            return []

        raw_levels = []

        for swing in swings:

            if swing.type == "LOW":

                raw_levels.append(
                    SupportResistanceLevel(
                        price=float(swing.price),
                        level_type="SUPPORT",
                        strength=1.0,
                        touches=1,
                        first_index=swing.index,
                        last_index=swing.index,
                        first_time=swing.time,
                        last_time=swing.time,
                        source="SWING_LOW",
                    )
                )

            elif swing.type == "HIGH":

                raw_levels.append(
                    SupportResistanceLevel(
                        price=float(swing.price),
                        level_type="RESISTANCE",
                        strength=1.0,
                        touches=1,
                        first_index=swing.index,
                        last_index=swing.index,
                        first_time=swing.time,
                        last_time=swing.time,
                        source="SWING_HIGH",
                    )
                )

        if not raw_levels:
            return []

        levels = self._cluster_levels(
            raw_levels
        )

        levels = self._calculate_strength(
            levels,
            candles,
        )

        levels = [
            level
            for level in levels
            if (
                level.touches
                >= self.min_touches
                and level.strength
                >= self.min_strength
            )
        ]

        levels.sort(
            key=lambda level: (
                level.strength,
                level.touches,
                level.last_index,
            ),
            reverse=True,
        )

        return levels[: self.max_levels]

    def _cluster_levels(
        self,
        raw_levels,
    ):

        clusters = []

        for level in sorted(
            raw_levels,
            key=lambda item: item.price,
        ):

            matched = None

            for cluster in clusters:

                if (
                    cluster.level_type
                    != level.level_type
                ):
                    continue

                if (
                    abs(
                        cluster.price
                        - level.price
                    )
                    <= self.tolerance
                ):

                    matched = cluster
                    break

            if matched is None:

                clusters.append(
                    SupportResistanceLevel(
                        price=level.price,
                        level_type=level.level_type,
                        strength=level.strength,
                        touches=level.touches,
                        first_index=level.first_index,
                        last_index=level.last_index,
                        first_time=level.first_time,
                        last_time=level.last_time,
                        source=level.source,
                    )
                )

                continue

            total_touches = (
                matched.touches
                + level.touches
            )

            matched.price = (
                (
                    matched.price
                    * matched.touches
                )
                + (
                    level.price
                    * level.touches
                )
            ) / total_touches

            matched.touches = total_touches

            matched.strength += (
                level.strength
            )

            if (
                level.first_index
                < matched.first_index
            ):

                matched.first_index = (
                    level.first_index
                )

                matched.first_time = (
                    level.first_time
                )

            if (
                level.last_index
                > matched.last_index
            ):

                matched.last_index = (
                    level.last_index
                )

                matched.last_time = (
                    level.last_time
                )

            matched.source = (
                "SWING_CLUSTER"
            )

        return clusters

    def _calculate_strength(
        self,
        levels,
        candles,
    ):

        if not candles:
            return levels

        last_index = len(candles) - 1

        for level in levels:

            touch_score = min(
                level.touches * 1.5,
                6.0,
            )

            age = max(
                0,
                last_index
                - level.last_index,
            )

            if age <= 20:
                recency_score = 2.0

            elif age <= 50:
                recency_score = 1.0

            else:
                recency_score = 0.5

            reaction_score = (
                self._reaction_score(
                    level,
                    candles,
                )
            )

            level.strength = round(
                touch_score
                + recency_score
                + reaction_score,
                2,
            )

        return levels

    def _reaction_score(
        self,
        level,
        candles,
    ):

        score = 0.0

        start = max(
            0,
            level.first_index,
        )

        for candle in candles[start:]:

            distance_high = abs(
                candle.high
                - level.price
            )

            distance_low = abs(
                candle.low
                - level.price
            )

            distance_close = abs(
                candle.close
                - level.price
            )

            if (
                distance_high
                <= self.tolerance
                or distance_low
                <= self.tolerance
                or distance_close
                <= self.tolerance
            ):

                score += 0.25

        return min(
            score,
            3.0,
        )

    def nearest_support(
        self,
        price,
        levels,
    ):

        supports = [
            level
            for level in levels
            if (
                level.level_type
                == "SUPPORT"
                and level.price < price
            )
        ]

        if not supports:
            return None

        return min(
            supports,
            key=lambda level:
            price - level.price,
        )

    def nearest_resistance(
        self,
        price,
        levels,
    ):

        resistances = [
            level
            for level in levels
            if (
                level.level_type
                == "RESISTANCE"
                and level.price > price
            )
        ]

        if not resistances:
            return None

        return min(
            resistances,
            key=lambda level:
            level.price - price,
        )

    def nearest_levels(
        self,
        price,
        levels,
    ):

        # Explicitly classify levels relative to
        # CURRENT PRICE.
        supports = [
            level
            for level in levels
            if (
                level.level_type
                == "SUPPORT"
                and level.price < price
            )
        ]

        resistances = [
            level
            for level in levels
            if (
                level.level_type
                == "RESISTANCE"
                and level.price > price
            )
        ]

        supports.sort(
            key=lambda level:
            price - level.price
        )

        resistances.sort(
            key=lambda level:
            level.price - price
        )

        return {
            "support": (
                supports[0]
                if supports
                else None
            ),
            "resistance": (
                resistances[0]
                if resistances
                else None
            ),
        }
