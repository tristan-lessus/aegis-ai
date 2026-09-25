from dataclasses import dataclass


@dataclass
class TradeSetup:
    direction: str
    confidence: int
    reasons: list


class ConfluenceEngine:

    def evaluate(
        self,
        structure=None,
        liquidity=False,
        displacement=False,
        fvg=False,
        mitigation=False,
        premium_discount=None,
        breaker_block=False,
        institutional_order_block=False,
    ):

        score = 0
        reasons = []

        # =====================================
        # STRUCTURE
        # =====================================

        if structure == "BULLISH":

            score += 20
            reasons.append("Bullish Structure")

        elif structure == "BEARISH":

            score += 20
            reasons.append("Bearish Structure")

        # =====================================
        # LIQUIDITY
        # =====================================

        if liquidity:

            score += 15
            reasons.append("Liquidity Sweep")

        # =====================================
        # DISPLACEMENT
        # =====================================

        if displacement:

            score += 20
            reasons.append("Displacement")

        # =====================================
        # FVG
        # =====================================

        if fvg:

            score += 15
            reasons.append("Fair Value Gap")

        # =====================================
        # MITIGATION
        # =====================================

        if mitigation:

            score += 15
            reasons.append("Mitigation")

        # =====================================
        # PREMIUM / DISCOUNT
        # =====================================

        if premium_discount == "DISCOUNT":

            score += 15
            reasons.append("Discount Zone")

        elif premium_discount == "PREMIUM":

            score += 15
            reasons.append("Premium Zone")

        # =====================================
        # BREAKER BLOCK
        # =====================================

        if breaker_block:

            score += 15
            reasons.append("Breaker Block")

        # =====================================
        # INSTITUTIONAL ORDER BLOCK
        # =====================================

        if institutional_order_block:

            score += 15
            reasons.append("Institutional Order Block")

        # =====================================
        # CAP SCORE
        # =====================================

        score = min(score, 100)

        direction = structure if structure else "NONE"

        return TradeSetup(
            direction=direction,
            confidence=score,
            reasons=reasons,
        )
