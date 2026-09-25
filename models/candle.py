from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class Candle:
    """
    Represents one market candle (OHLCV).

    Candle timestamps are stored as timezone-aware UTC datetimes.
    """

    time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    def __post_init__(self):
        if self.time.tzinfo is None:
            self.time = self.time.replace(tzinfo=timezone.utc)
        else:
            self.time = self.time.astimezone(timezone.utc)
