from dataclasses import dataclass


@dataclass
class ValidationResult:
    valid: bool
    reasons: list
    mtf_status: str = "INSUFFICIENT_DATA"
    execution_type: str = "UNKNOWN"
    risk_mode: str = "NORMAL"


class TradeValidator:

    def __init__(
        self,
        min_risk_reward: float = 1.5,
    ):
        self.min_risk_reward = min_risk_reward

    def validate(
        self,
        direction: str,
        entry: float,
        stop_loss: float,
        take_profit: float,
        risk_reward: float,
        mtf_status: str = "INSUFFICIENT_DATA",
        execution_type: str = "UNKNOWN",
        risk_mode: str = "NORMAL",
    ):

        reasons = []

        direction = direction.upper()
        mtf_status = mtf_status.upper()
        execution_type = execution_type.upper()
        risk_mode = risk_mode.upper()

        # =========================================================
        # BASIC VALIDATION
        # =========================================================

        if direction not in (
            "BULLISH",
            "BEARISH",
        ):
            reasons.append(
                "Invalid direction"
            )

        if entry <= 0:
            reasons.append(
                "Invalid entry"
            )

        if stop_loss <= 0:
            reasons.append(
                "Invalid stop loss"
            )

        if take_profit <= 0:
            reasons.append(
                "Invalid take profit"
            )

        # =========================================================
        # DIRECTIONAL VALIDATION
        # =========================================================

        if direction == "BULLISH":

            if stop_loss >= entry:
                reasons.append(
                    "Bullish SL must be below entry"
                )

            if take_profit <= entry:
                reasons.append(
                    "Bullish TP must be above entry"
                )

        elif direction == "BEARISH":

            if stop_loss <= entry:
                reasons.append(
                    "Bearish SL must be above entry"
                )

            if take_profit >= entry:
                reasons.append(
                    "Bearish TP must be below entry"
                )

        # =========================================================
        # RISK / REWARD
        # =========================================================

        if risk_reward < self.min_risk_reward:

            reasons.append(
                f"RR below minimum "
                f"{self.min_risk_reward}"
            )

        # =========================================================
        # MTF CONTEXT
        #
        # MTF status does NOT automatically invalidate
        # a structurally valid trade.
        # =========================================================

        valid_mtf_statuses = {
            "ALIGNED",
            "PARTIAL",
            "CONFLICTING",
            "COUNTERTREND",
            "INSUFFICIENT_DATA",
        }

        if mtf_status not in valid_mtf_statuses:

            reasons.append(
                f"Unknown MTF status: {mtf_status}"
            )

        # =========================================================
        # FINAL VALIDATION
        # =========================================================

        return ValidationResult(
            valid=len(reasons) == 0,
            reasons=reasons,
            mtf_status=mtf_status,
            execution_type=execution_type,
            risk_mode=risk_mode,
        )
