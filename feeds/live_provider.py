import requests
import pandas as pd

from models.candle import Candle
from feeds.base_provider import BaseProvider


class LiveProvider(BaseProvider):
    """
    Live market data provider using Twelve Data.

    All candle timestamps are normalized to timezone-aware UTC.
    """

    BASE_URL = "https://api.twelvedata.com/time_series"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 500,
    ):
        interval_map = {
            "M1": "1min",
            "M5": "5min",
            "M15": "15min",
            "M30": "30min",
            "H1": "1h",
            "H4": "4h",
            "D1": "1day",
        }

        if timeframe not in interval_map:
            raise ValueError(
                f"Unsupported timeframe: {timeframe}"
            )

        params = {
            "symbol": symbol,
            "interval": interval_map[timeframe],
            "outputsize": count,
            "apikey": self.api_key,
            "timezone": "UTC",
        }

        response = requests.get(
            self.BASE_URL,
            params=params,
            timeout=15,
        )

        data = response.json()

        if response.status_code != 200:
            raise Exception(data)

        if "values" not in data:
            raise Exception(data)

        candles = []

        for row in reversed(data["values"]):
            timestamp = pd.to_datetime(
                row["datetime"],
                utc=True,
            ).to_pydatetime()

            candles.append(
                Candle(
                    time=timestamp,
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row.get("volume", 0)),
                )
            )

        if not candles:
            raise Exception(
                f"No candles returned for {symbol} {timeframe}"
            )

        return candles
