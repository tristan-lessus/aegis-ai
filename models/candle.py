from dataclasses import dataclass
from datetime import datetime


@dataclass
class Candle:
    """
    Represents one market candle (OHLCV).
    """

    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
