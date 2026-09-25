from dataclasses import dataclass


@dataclass
class RiskResult:
    balance: float
    risk_percent: float
    risk_amount: float
    entry: float
    stop_loss: float
    stop_distance: float
    position_size: float


class RiskManager:

    def __init__(
        self,
        risk_percent: float = 1.0,
        min_risk_percent: float = 0.1,
        max_risk_percent: float = 2.0,
    ):
        self.risk_percent = risk_percent
        self.min_risk_percent = min_risk_percent
        self.max_risk_percent = max_risk_percent

    def calculate(
        self,
        balance: float,
        entry: float,
        stop_loss: float,
    ) -> RiskResult:

        if balance <= 0:
            raise ValueError("Account balance must be greater than 0")

        if entry <= 0 or stop_loss <= 0:
            raise ValueError("Entry and stop loss must be greater than 0")

        if entry == stop_loss:
            raise ValueError("Entry and stop loss cannot be equal")

        if not (
            self.min_risk_percent
            <= self.risk_percent
            <= self.max_risk_percent
        ):
            raise ValueError(
                f"Risk must be between "
                f"{self.min_risk_percent}% and "
                f"{self.max_risk_percent}%"
            )

        risk_amount = balance * (
            self.risk_percent / 100
        )

        stop_distance = abs(entry - stop_loss)

        position_size = (
            risk_amount / stop_distance
        )

        return RiskResult(
            balance=round(balance, 2),
            risk_percent=round(self.risk_percent, 2),
            risk_amount=round(risk_amount, 2),
            entry=round(entry, 2),
            stop_loss=round(stop_loss, 2),
            stop_distance=round(stop_distance, 2),
            position_size=round(position_size, 4),
)

