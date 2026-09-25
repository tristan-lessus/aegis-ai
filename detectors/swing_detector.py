from dataclasses import dataclass


@dataclass
class SwingPoint:
    index: int
    time: object
    price: float
    type: str      # HIGH or LOW


class SwingDetector:

    def __init__(self, lookback=3):
        self.lookback = lookback

    def detect(self, candles):

        swings = []

        for i in range(self.lookback, len(candles) - self.lookback):

            current = candles[i]

            high = current.high
            low = current.low

            left = candles[i - self.lookback:i]
            right = candles[i + 1:i + self.lookback + 1]

            is_high = all(high > c.high for c in left + right)
            is_low = all(low < c.low for c in left + right)

            # Ignore candles that qualify as both.
            if is_high and is_low:
                continue

            if is_high:
                swings.append(
                    SwingPoint(
                        index=i,
                        time=current.time,
                        price=high,
                        type="HIGH"
                    )
                )

            elif is_low:
                swings.append(
                    SwingPoint(
                        index=i,
                        time=current.time,
                        price=low,
                        type="LOW"
                    )
                )

        return self._filter_consecutive(swings)

    def _filter_consecutive(self, swings):

        if not swings:
            return []

        filtered = [swings[0]]

        for swing in swings[1:]:

            last = filtered[-1]

            # Keep alternating HIGH -> LOW -> HIGH...
            if swing.type != last.type:
                filtered.append(swing)
                continue

            # Two HIGHs in a row: keep the higher one.
            if swing.type == "HIGH":

                if swing.price > last.price:
                    filtered[-1] = swing

            # Two LOWs in a row: keep the lower one.
            else:

                if swing.price < last.price:
                    filtered[-1] = swing

        return filtered
