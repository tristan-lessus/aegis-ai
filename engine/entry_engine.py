from dataclasses import dataclass
from statistics import mean


@dataclass
class TradeSetup:
    direction: str
    entry: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    risk_reward: float
    entry_zone: str = "NONE"
    setup_type: str = "WAIT"
    source_time: object = None
    status: str = "WAIT"
    reason: str = ""


class EntryEngine:

    def __init__(
        self,
        buffer=0.30,
        atr_period=14,
        max_zone_atr=2.0,
        minimum_rr=1.5,
        max_zone_age_bars=30,
    ):

        self.buffer = float(buffer)

        self.atr_period = int(
            atr_period
        )

        self.max_zone_atr = float(
            max_zone_atr
        )

        self.minimum_rr = float(
            minimum_rr
        )

        self.max_zone_age_bars = int(
            max_zone_age_bars
        )

    # ==========================================================
    # ATR
    # ==========================================================

    def _calculate_atr(
        self,
        candles,
    ):

        if len(candles) < 2:
            return 0.0

        true_ranges = []

        start = max(
            1,
            len(candles)
            - self.atr_period,
        )

        for i in range(
            start,
            len(candles),
        ):

            current = candles[i]
            previous = candles[i - 1]

            tr = max(
                current.high
                - current.low,

                abs(
                    current.high
                    - previous.close
                ),

                abs(
                    current.low
                    - previous.close
                ),
            )

            true_ranges.append(
                tr
            )

        if not true_ranges:
            return 0.0

        return mean(
            true_ranges
        )

    # ==========================================================
    # ZONE HELPERS
    # ==========================================================

    def _zone_bounds(
        self,
        zone,
    ):

        if zone is None:
            return None

        low = getattr(
            zone,
            "low",
            None,
        )

        high = getattr(
            zone,
            "high",
            None,
        )

        if low is None:

            low = getattr(
                zone,
                "bottom",
                None,
            )

        if high is None:

            high = getattr(
                zone,
                "top",
                None,
            )

        if low is None or high is None:
            return None

        try:

            low = float(
                low
            )

            high = float(
                high
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

        if low > high:

            low, high = (
                high,
                low,
            )

        if low <= 0 or high <= 0:
            return None

        return (
            low,
            high,
        )

    def _zone_direction(
        self,
        zone,
    ):

        direction = getattr(
            zone,
            "direction",
            None,
        )

        if direction in (
            "BULLISH",
            "BEARISH",
        ):

            return direction

        return None

    def _zone_index(
        self,
        zone,
    ):

        for attribute in (
            "confirmation_index",
            "retest_index",
            "index",
            "start_index",
        ):

            value = getattr(
                zone,
                attribute,
                None,
            )

            if value is None:
                continue

            try:

                return int(
                    value
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

        return -1

    def _zone_source_time(
        self,
        zone,
    ):

        for attribute in (
            "confirmation_time",
            "retest_time",
            "time",
            "start_time",
        ):

            value = getattr(
                zone,
                attribute,
                None,
            )

            if value is not None:
                return value

        return None

    def _zone_is_fresh(
        self,
        zone,
        candles,
    ):

        if not candles:
            return False

        index = self._zone_index(
            zone
        )

        if index < 0:
            return False

        latest = (
            len(candles)
            - 1
        )

        age = (
            latest
            - index
        )

        if age < 0:
            return False

        return (
            age
            <= self.max_zone_age_bars
        )

    def _zone_is_active(
        self,
        zone,
    ):

        if getattr(
            zone,
            "mitigated",
            False,
        ):

            return False

        if getattr(
            zone,
            "invalidated",
            False,
        ):

            return False

        if getattr(
            zone,
            "consumed",
            False,
        ):

            return False

        if (
            getattr(
                zone,
                "active",
                True,
            )
            is False
        ):

            return False

        return True

    def _zone_is_realistic(
        self,
        zone,
        direction,
        current_price,
        atr,
    ):

        bounds = self._zone_bounds(
            zone
        )

        if bounds is None:
            return False

        low, high = bounds

        if direction == "BULLISH":

            if low >= current_price:
                return False

            distance = (
                current_price
                - high
            )

        elif direction == "BEARISH":

            if high <= current_price:
                return False

            distance = (
                low
                - current_price
            )

        else:

            return False

        if distance < 0:
            distance = 0

        if atr > 0:

            if (
                distance
                > (
                    atr
                    * self.max_zone_atr
                )
            ):

                return False

        return True

    def _zone_quality(
        self,
        zone,
        zone_type,
        current_price,
    ):

        score = 0.0

        if (
            zone_type
            == "INSTITUTIONAL_ORDER_BLOCK"
        ):

            score += 35

        elif (
            zone_type
            == "BREAKER_BLOCK"
        ):

            score += 30

        elif (
            zone_type
            == "FAIR_VALUE_GAP"
        ):

            score += 20

        if getattr(
            zone,
            "confirmed",
            False,
        ):

            score += 10

        strength = getattr(
            zone,
            "strength",
            None,
        )

        if strength is not None:

            try:

                score += min(
                    float(strength),
                    10.0,
                )

            except (
                TypeError,
                ValueError,
            ):

                pass

        bounds = self._zone_bounds(
            zone
        )

        if bounds:

            low, high = bounds

            midpoint = (
                low + high
            ) / 2.0

            distance = abs(
                current_price
                - midpoint
            )

            if distance <= 1.0:

                score += 5

            elif distance <= 2.0:

                score += 3

        return score

    # ==========================================================
    # FIND BEST ENTRY ZONE
    # ==========================================================

    def _find_best_zone(
        self,
        direction,
        current_price,
        atr,
        order_blocks,
        breaker_blocks,
        fvg_events,
        candles,
    ):

        sources = [
            (
                order_blocks,
                "INSTITUTIONAL_ORDER_BLOCK",
                1,
            ),
            (
                breaker_blocks,
                "BREAKER_BLOCK",
                2,
            ),
            (
                fvg_events,
                "FAIR_VALUE_GAP",
                3,
            ),
        ]

        candidates = []

        for zones, zone_type, priority in sources:

            if not zones:
                continue

            for zone in zones:

                zone_direction = (
                    self._zone_direction(
                        zone
                    )
                )

                if (
                    zone_direction
                    != direction
                ):

                    continue

                if not self._zone_is_active(
                    zone
                ):

                    continue

                if not self._zone_is_fresh(
                    zone,
                    candles,
                ):

                    continue

                if not self._zone_is_realistic(
                    zone,
                    direction,
                    current_price,
                    atr,
                ):

                    continue

                bounds = self._zone_bounds(
                    zone
                )

                if bounds is None:
                    continue

                quality = (
                    self._zone_quality(
                        zone,
                        zone_type,
                        current_price,
                    )
                )

                low, high = bounds

                midpoint = (
                    low + high
                ) / 2.0

                distance = abs(
                    current_price
                    - midpoint
                )

                candidates.append(
                    (
                        quality,
                        -distance,
                        -priority,
                        zone,
                        zone_type,
                    )
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                item[0],
                item[1],
                item[2],
            ),
            reverse=True,
        )

        best = candidates[0]

        return (
            best[3],
            best[4],
        )

    # ==========================================================
    # TARGETS
    # ==========================================================

    def _find_targets(
        self,
        direction,
        entry,
        support_resistance,
    ):

        if not support_resistance:
            return []

        targets = []

        for level in support_resistance:

            try:

                price = float(
                    level.price
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            level_type = getattr(
                level,
                "level_type",
                None,
            )

            if direction == "BULLISH":

                if (
                    level_type
                    != "RESISTANCE"
                ):

                    continue

                if price <= entry:
                    continue

            elif direction == "BEARISH":

                if (
                    level_type
                    != "SUPPORT"
                ):

                    continue

                if price >= entry:
                    continue

            else:

                continue

            targets.append(
                level
            )

        if direction == "BULLISH":

            targets.sort(
                key=lambda level:
                float(level.price)
            )

        else:

            targets.sort(
                key=lambda level:
                float(level.price),
                reverse=True,
            )

        return self._remove_duplicate_targets(
            targets
        )

    def _remove_duplicate_targets(
        self,
        targets,
    ):

        result = []

        for target in targets:

            price = float(
                target.price
            )

            duplicate = False

            for existing in result:

                existing_price = float(
                    existing.price
                )

                if (
                    abs(
                        price
                        - existing_price
                    )
                    <= self.buffer
                ):

                    duplicate = True

                    break

            if not duplicate:

                result.append(
                    target
                )

        return result

    # ==========================================================
    # SMART TARGET SELECTION
    # ==========================================================

    def _select_targets(
        self,
        direction,
        entry,
        stop_loss,
        targets,
    ):

        if not targets:
            return None

        valid_targets = []

        for target in targets:

            try:

                price = float(
                    target.price
                )

            except (
                TypeError,
                ValueError,
            ):

                continue

            rr = self._calculate_rr(
                entry=entry,
                stop_loss=stop_loss,
                take_profit=price,
            )

            if rr < self.minimum_rr:
                continue

            valid_targets.append(
                (
                    target,
                    rr,
                )
            )

        if not valid_targets:

            return None

        # Targets are already ordered from nearest
        # to farthest opposing level.
        #
        # Therefore the first target that satisfies
        # minimum RR becomes TP1.

        tp1_target, tp1_rr = (
            valid_targets[0]
        )

        tp2 = 0.0

        # TP2 is the next farther valid target.
        if len(valid_targets) >= 2:

            tp2_target, _ = (
                valid_targets[1]
            )

            tp2 = float(
                tp2_target.price
            )

        return (
            float(
                tp1_target.price
            ),
            tp2,
            tp1_rr,
        )

    # ==========================================================
    # STOP
    # ==========================================================

    def _calculate_stop(
        self,
        direction,
        zone_low,
        zone_high,
        swing_high,
        swing_low,
    ):

        if direction == "BULLISH":

            structural_low = (
                zone_low
            )

            if swing_low is not None:

                swing_low = float(
                    swing_low
                )

                if (
                    swing_low < zone_low
                    and (
                        zone_low
                        - swing_low
                    )
                    <= max(
                        zone_high
                        - zone_low,
                        self.buffer * 4,
                    )
                ):

                    structural_low = (
                        swing_low
                    )

            return (
                structural_low
                - self.buffer
            )

        structural_high = (
            zone_high
        )

        if swing_high is not None:

            swing_high = float(
                swing_high
            )

            if (
                swing_high > zone_high
                and (
                    swing_high
                    - zone_high
                )
                <= max(
                    zone_high
                    - zone_low,
                    self.buffer * 4,
                )
            ):

                structural_high = (
                    swing_high
                )

        return (
            structural_high
            + self.buffer
        )

    # ==========================================================
    # RR
    # ==========================================================

    def _calculate_rr(
        self,
        entry,
        stop_loss,
        take_profit,
    ):

        risk = abs(
            entry
            - stop_loss
        )

        if risk <= 0:
            return 0.0

        reward = abs(
            take_profit
            - entry
        )

        return (
            reward / risk
        )

    # ==========================================================
    # WAIT
    # ==========================================================

    def _wait_setup(
        self,
        direction,
        reason,
    ):

        return TradeSetup(
            direction=direction,
            entry=0.0,
            stop_loss=0.0,
            take_profit_1=0.0,
            take_profit_2=0.0,
            risk_reward=0.0,
            entry_zone="NONE",
            setup_type="WAIT",
            source_time=None,
            status="WAIT",
            reason=reason,
        )

    # ==========================================================
    # MAIN
    # ==========================================================

    def generate(
        self,
        direction,
        current_price,
        swing_high=None,
        swing_low=None,
        order_blocks=None,
        breaker_blocks=None,
        fvg_events=None,
        candles=None,
        support_resistance=None,
    ):

        if direction not in (
            "BULLISH",
            "BEARISH",
        ):

            return self._wait_setup(
                direction,
                "No directional bias",
            )

        if current_price is None:

            return self._wait_setup(
                direction,
                "No current price",
            )

        current_price = float(
            current_price
        )

        candles = candles or []

        atr = self._calculate_atr(
            candles
        )

        # ------------------------------------------------------
        # 1. Find fresh zone
        # ------------------------------------------------------

        zone_result = (
            self._find_best_zone(
                direction=direction,
                current_price=current_price,
                atr=atr,
                order_blocks=order_blocks,
                breaker_blocks=breaker_blocks,
                fvg_events=fvg_events,
                candles=candles,
            )
        )

        if zone_result is None:

            return self._wait_setup(
                direction,
                "No realistic fresh active entry zone",
            )

        zone, zone_name = zone_result

        bounds = self._zone_bounds(
            zone
        )

        if bounds is None:

            return self._wait_setup(
                direction,
                "Invalid entry zone",
            )

        zone_low, zone_high = bounds

        # ------------------------------------------------------
        # 2. Entry
        # ------------------------------------------------------

        entry = (
            zone_low
            + zone_high
        ) / 2.0

        # ------------------------------------------------------
        # 3. Structural stop
        # ------------------------------------------------------

        stop_loss = (
            self._calculate_stop(
                direction=direction,
                zone_low=zone_low,
                zone_high=zone_high,
                swing_high=swing_high,
                swing_low=swing_low,
            )
        )

        if direction == "BULLISH":

            if stop_loss >= entry:

                return self._wait_setup(
                    direction,
                    "Bullish stop is not below entry",
                )

        else:

            if stop_loss <= entry:

                return self._wait_setup(
                    direction,
                    "Bearish stop is not above entry",
                )

        # ------------------------------------------------------
        # 4. Find opposing targets
        # ------------------------------------------------------

        targets = self._find_targets(
            direction=direction,
            entry=entry,
            support_resistance=(
                support_resistance or []
            ),
        )

        if not targets:

            return self._wait_setup(
                direction,
                "No valid opposing S/R target",
            )

        # ------------------------------------------------------
        # 5. SMART TP SELECTION
        # ------------------------------------------------------
        #
        # Do not blindly use the nearest S/R level.
        #
        # Skip targets that produce RR below the
        # configured minimum. The nearest target that
        # satisfies minimum RR becomes TP1.
        #
        # The next farther valid target becomes TP2.

        target_selection = (
            self._select_targets(
                direction=direction,
                entry=entry,
                stop_loss=stop_loss,
                targets=targets,
            )
        )

        if target_selection is None:

            nearest_rr = 0.0

            if targets:

                nearest_rr = (
                    self._calculate_rr(
                        entry=entry,
                        stop_loss=stop_loss,
                        take_profit=float(
                            targets[0].price
                        ),
                    )
                )

            return self._wait_setup(
                direction,
                (
                    "No opposing S/R target "
                    "meets minimum RR "
                    f"({nearest_rr:.2f} < "
                    f"{self.minimum_rr:.2f})"
                ),
            )

        (
            tp1,
            tp2,
            rr,
        ) = target_selection

        # ------------------------------------------------------
        # 6. Validate target direction
        # ------------------------------------------------------

        if direction == "BULLISH":

            if tp1 <= entry:

                return self._wait_setup(
                    direction,
                    "Bullish TP1 is invalid",
                )

            if (
                tp2 != 0.0
                and tp2 <= tp1
            ):

                return self._wait_setup(
                    direction,
                    "Bullish TP2 is invalid",
                )

        else:

            if tp1 >= entry:

                return self._wait_setup(
                    direction,
                    "Bearish TP1 is invalid",
                )

            if (
                tp2 != 0.0
                and tp2 >= tp1
            ):

                return self._wait_setup(
                    direction,
                    "Bearish TP2 is invalid",
                )

        # ------------------------------------------------------
        # 7. Final RR check
        # ------------------------------------------------------

        rr = self._calculate_rr(
            entry=entry,
            stop_loss=stop_loss,
            take_profit=tp1,
        )

        if rr < self.minimum_rr:

            return self._wait_setup(
                direction,
                (
                    "Selected TP1 gives insufficient RR "
                    f"({rr:.2f} < "
                    f"{self.minimum_rr:.2f})"
                ),
            )

        # ------------------------------------------------------
        # 8. Valid setup
        # ------------------------------------------------------

        return TradeSetup(
            direction=direction,

            entry=round(
                entry,
                2,
            ),

            stop_loss=round(
                stop_loss,
                2,
            ),

            take_profit_1=round(
                tp1,
                2,
            ),

            take_profit_2=round(
                tp2,
                2,
            ),

            risk_reward=round(
                rr,
                2,
            ),

            entry_zone=zone_name,

            setup_type="LIMIT",

            source_time=(
                self._zone_source_time(
                    zone
                )
            ),

            status="VALID",

            reason=(
                "Fresh active structural zone "
                "with opposing S/R target meeting "
                f"minimum RR {self.minimum_rr:.2f}"
            ),
        )
