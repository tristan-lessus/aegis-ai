from dataclasses import dataclass


@dataclass
class ConfidenceResult:
    score: int
    reasons: list


class ConfidenceEngine:

    def calculate(
        self,
        structure=False,
        liquidity=False,
        displacement=False,
        fvg=False,
        mitigation=False,
        premium_discount=False,
        order_block=False,
        session=False,
    ):

        score = 0
        reasons = []

        if structure:
            score += 25
            reasons.append("Structure")

        if liquidity:
            score += 15
            reasons.append("Liquidity Sweep")

        if displacement:
            score += 15
            reasons.append("Displacement")

        if fvg:
            score += 15
            reasons.append("Fair Value Gap")

        if mitigation:
            score += 10
            reasons.append("Mitigation")

        if premium_discount:
            score += 10
            reasons.append("Premium / Discount")

        if order_block:
            score += 5
            reasons.append("Order Block")

        if session:
            score += 5
            reasons.append("Trading Session")

        score = min(score, 100)

        return ConfidenceResult(
            score=score,
            reasons=reasons
        )
