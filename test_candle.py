from datetime import datetime
from models.candle import Candle


candle = Candle(
    time=datetime.now(),
    open=3345.2,
    high=3351.8,
    low=3342.1,
    close=3349.7,
    volume=1425
)

print(candle)
