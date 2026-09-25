from dataclasses import dataclass


@dataclass
class Signal:
    direction: str
    confidence: int
    reasons: list

    entry: float = 0.0
    stop_loss: float = 0.0
    take_profit_1: float = 0.0
    take_profit_2: float = 0.0
    risk_reward: float = 0.0

    entry_zone: str = "NONE"
    setup_type: str = "WAIT"
    entry_source_time: object = None

    trade_valid: bool = False
    validation_reasons: list = None
    setup_status: str = "WAIT"

    # MTF context
    h1_bias: str = "UNKNOWN"
    m15_bias: str = "UNKNOWN"
    mtf_alignment: str = "INSUFFICIENT_DATA"
    mtf_status: str = "INSUFFICIENT_DATA"
    htf_conflict: bool = False

    # Execution classification
    execution_type: str = "UNKNOWN"
    risk_mode: str = "NORMAL"


class SignalEngine:

    def generate(
        self,
        structure_events=None,
        liquidity_events=None,
        displacement_events=None,
        fvg_events=None,
        mitigation_events=None,
        zone="UNKNOWN",
        breaker_blocks=None,
        institutional_order_blocks=None,
        mtf_context=None,
    ):

        structure_events = structure_events or []
        liquidity_events = liquidity_events or []
        displacement_events = displacement_events or []
        fvg_events = fvg_events or []
        mitigation_events = mitigation_events or []
        breaker_blocks = breaker_blocks or []
        institutional_order_blocks = (
            institutional_order_blocks or []
        )

        mtf_context = mtf_context or {}

        h1 = mtf_context.get("h1", {})
        m15 = mtf_context.get("m15", {})

        h1_bias = h1.get("bias", "UNKNOWN")
        m15_bias = m15.get("bias", "UNKNOWN")
        htf_alignment = mtf_context.get(
            "alignment",
            "INSUFFICIENT_DATA",
        )

        reasons = []

        direction = "NONE"

        # =========================================================
        # M5 EXECUTION DIRECTION
        # =========================================================

        if structure_events:

            latest_structure = structure_events[-1]

            structure_direction = getattr(
                latest_structure,
                "direction",
                "NONE",
            )

            if structure_direction in (
                "BULLISH",
                "BEARISH",
            ):
                direction = structure_direction

                reasons.append(
                    f"{structure_direction.title()} Structure"
                )

        # =========================================================
        # MTF CLASSIFICATION
        # =========================================================

        known_htfs = [
            bias
            for bias in (h1_bias, m15_bias)
            if bias in ("BULLISH", "BEARISH")
        ]

        aligned_htfs = [
            bias
            for bias in known_htfs
            if bias == direction
        ]

        opposing_htfs = [
            bias
            for bias in known_htfs
            if bias != direction
        ]

        htf_conflict = bool(
            direction in ("BULLISH", "BEARISH")
            and opposing_htfs
        )

        if direction in ("BULLISH", "BEARISH"):

            # Both H1 and M15 support execution
            if (
                h1_bias == direction
                and m15_bias == direction
            ):
                mtf_status = "ALIGNED"
                execution_type = "WITH_TREND"
                risk_mode = "NORMAL"

                reasons.append(
                    "Higher-Timeframe Alignment"
                )

            # Both H1 and M15 oppose execution
            elif (
                h1_bias in ("BULLISH", "BEARISH")
                and m15_bias in ("BULLISH", "BEARISH")
                and h1_bias != direction
                and m15_bias != direction
            ):
                mtf_status = "COUNTERTREND"
                execution_type = "COUNTERTREND"
                risk_mode = "CAUTION"

                reasons.append(
                    "Countertrend Execution"
                )

            # H1 and M15 disagree with each other
            elif (
                h1_bias in ("BULLISH", "BEARISH")
                and m15_bias in ("BULLISH", "BEARISH")
                and h1_bias != m15_bias
            ):
                mtf_status = "CONFLICTING"
                execution_type = "MIXED_TIMEFRAME"
                risk_mode = "CAUTION"

                reasons.append(
                    "Higher-Timeframe Conflict"
                )

            # One HTF agrees and the other is unavailable
            elif aligned_htfs:
                mtf_status = "PARTIAL"
                execution_type = "WITH_PARTIAL_CONFIRMATION"
                risk_mode = "NORMAL"

                reasons.append(
                    "Partial Higher-Timeframe Support"
                )

            # HTF information exists but opposes M5
            elif opposing_htfs:
                mtf_status = "COUNTERTREND"
                execution_type = "COUNTERTREND"
                risk_mode = "CAUTION"

                reasons.append(
                    "Higher-Timeframe Opposition"
                )

            else:
                mtf_status = "INSUFFICIENT_DATA"
                execution_type = "UNKNOWN"
                risk_mode = "CAUTION"

        else:

            mtf_status = "INSUFFICIENT_DATA"
            execution_type = "UNKNOWN"
            risk_mode = "CAUTION"

        # =========================================================
        # LIQUIDITY
        # =========================================================

        aligned_liquidity = []

        for event in liquidity_events:

            if not getattr(
                event,
                "confirmed",
                True,
            ):
                continue

            event_direction = getattr(
                event,
                "direction",
                None,
            )

            if (
                direction == "NONE"
                or event_direction == direction
            ):
                aligned_liquidity.append(event)

        if aligned_liquidity:
            reasons.append("Liquidity Sweep")

        # =========================================================
        # DISPLACEMENT
        # =========================================================

        aligned_displacement = []

        for event in displacement_events:

            event_direction = getattr(
                event,
                "direction",
                None,
            )

            if (
                direction == "NONE"
                or event_direction == direction
            ):
                aligned_displacement.append(event)

        if aligned_displacement:
            reasons.append("Displacement")

        # =========================================================
        # FVG
        # =========================================================

        aligned_fvg = []

        for event in fvg_events:

            event_direction = getattr(
                event,
                "direction",
                None,
            )

            if (
                direction == "NONE"
                or event_direction == direction
            ):
                aligned_fvg.append(event)

        if aligned_fvg:
            reasons.append("Fair Value Gap")

        # =========================================================
        # MITIGATION
        # =========================================================

        if mitigation_events:
            reasons.append("Mitigation")

        # =========================================================
        # PREMIUM / DISCOUNT
        # =========================================================

        if (
            direction == "BULLISH"
            and zone == "DISCOUNT"
        ):
            reasons.append("Discount Zone")

        elif (
            direction == "BEARISH"
            and zone == "PREMIUM"
        ):
            reasons.append("Premium Zone")

        # =========================================================
        # BREAKER BLOCK
        # =========================================================

        aligned_breakers = [
            breaker
            for breaker in breaker_blocks
            if getattr(
                breaker,
                "direction",
                None,
            ) == direction
            and getattr(
                breaker,
                "confirmed",
                False,
            )
        ]

        if aligned_breakers:
            reasons.append("Breaker Block")

        # =========================================================
        # INSTITUTIONAL ORDER BLOCK
        # =========================================================

        aligned_obs = [
            ob
            for ob in institutional_order_blocks
            if getattr(
                ob,
                "direction",
                None,
            ) == direction
            and not getattr(
                ob,
                "mitigated",
                False,
            )
        ]

        if aligned_obs:
            reasons.append(
                "Institutional Order Block"
            )

        # =========================================================
        # BASE SCORE
        # =========================================================

        score = 0

        if structure_events:
            score += 25

        if aligned_liquidity:
            score += 20

        if aligned_displacement:
            score += 20

        if aligned_fvg:
            score += 10

        if (
            direction == "BULLISH"
            and zone == "DISCOUNT"
        ) or (
            direction == "BEARISH"
            and zone == "PREMIUM"
        ):
            score += 10

        if aligned_breakers:
            score += 10

        if aligned_obs:
            score += 10

        # =========================================================
        # MTF SCORE
        # =========================================================

        if (
            direction in ("BULLISH", "BEARISH")
            and h1_bias == direction
            and m15_bias == direction
        ):
            score += 15

        elif (
            direction in ("BULLISH", "BEARISH")
            and (
                h1_bias == direction
                or m15_bias == direction
            )
        ):
            score += 7

        elif htf_conflict:
            score -= 15

        # Strong countertrend penalty
        if (
            direction in ("BULLISH", "BEARISH")
            and h1_bias in ("BULLISH", "BEARISH")
            and m15_bias in ("BULLISH", "BEARISH")
            and h1_bias != direction
            and m15_bias != direction
        ):
            score -= 20

        score = max(
            0,
            min(score, 100),
        )

        # =========================================================
        # CORE EXECUTION REQUIREMENTS
        # =========================================================

        required_core = (
            bool(structure_events)
            and bool(aligned_liquidity)
            and bool(aligned_displacement)
        )

        if not required_core:

            direction = "NONE"

            score = min(
                score,
                45,
            )

            execution_type = "UNKNOWN"
            risk_mode = "CAUTION"

        # =========================================================
        # FINAL SIGNAL
        # =========================================================

        return Signal(
            direction=direction,
            confidence=score,
            reasons=reasons,
            validation_reasons=[],

            h1_bias=h1_bias,
            m15_bias=m15_bias,
            mtf_alignment=htf_alignment,
            mtf_status=mtf_status,
            htf_conflict=htf_conflict,

            execution_type=execution_type,
            risk_mode=risk_mode,
        )
