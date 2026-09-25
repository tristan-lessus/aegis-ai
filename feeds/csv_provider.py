import pandas as pd
from pathlib import Path
from models.candle import Candle
from feeds.base_provider import BaseProvider


class CSVProvider(BaseProvider):

    def __init__(self, data_folder="datasets"):
        self.data_folder = Path(data_folder)

    def get_candles(self, symbol: str, timeframe: str, count: int = 500):

        filename = self.data_folder / f"{symbol}_{timeframe}.csv"

        if not filename.exists():
            raise FileNotFoundError(f"{filename} not found")

        df = pd.read_csv(filename)

        required = ["time", "open", "high", "low", "close", "volume"]

        for col in required:
            if col not in df.columns:
                raise ValueError(f"Missing column: {col}")

        candles = []

        for _, row in df.tail(count).iterrows():
            candles.append(
                Candle(
                    time=pd.to_datetime(row["time"]),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"])
                )
            )

        return candles
