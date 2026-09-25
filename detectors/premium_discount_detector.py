from dataclasses import dataclass


@dataclass
class PremiumDiscountZone:
    swing_high: float
    swing_low: float
    equilibrium: float
    current_price: float
    zone: str


class PremiumDiscountDetector:

    def detect(self, swings, current_price):

        if not swings:
            return None

        highs = [
            s.price
            for s in swings
            if s.type == "HIGH"
        ]

        lows = [
            s.price
            for s in swings
            if s.type == "LOW"
        ]

        if not highs or not lows:
            return None

        swing_high = max(highs)
        swing_low = min(lows)

        equilibrium = (swing_high + swing_low) / 2

        zone = (
            "DISCOUNT"
            if current_price < equilibrium
            else "PREMIUM"
        )

        return PremiumDiscountZone(
            swing_high=round(swing_high, 2),
            swing_low=round(swing_low, 2),
            equilibrium=round(equilibrium, 2),
            current_price=round(current_price, 2),
            zone=zone,
        )
