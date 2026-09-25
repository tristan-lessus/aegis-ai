from abc import ABC, abstractmethod
from typing import List
from models.candle import Candle


class BaseProvider(ABC):
    """
    Abstract market data provider.
    Every provider must return a list of Candle objects.
    """

    @abstractmethod
    def get_candles(
        self,
        symbol: str,
        timeframe: str,
        count: int = 500
    ) -> List[Candle]:
        """
        Return the latest candles.

        Args:
            symbol: e.g. XAUUSD, US500
            timeframe: e.g. M5, M15, H1
            count: number of candles

        Returns:
            List[Candle]
        """
        pass
