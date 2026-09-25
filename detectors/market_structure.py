from typing import List


class MarketStructure:

    def __init__(self):
        self.trend = "UNKNOWN"

    def analyze(self, swings: List[dict]):

        events = []

        if len(swings) < 4:
            return events

        previous_high = None
        previous_low = None

        for swing in swings:

            t = swing["type"]

            if t in ("HH", "LH"):

                if previous_high is None:
                    previous_high = swing
                    continue

                if swing["price"] > previous_high["price"]:

                    if self.trend in ("BEARISH", "UNKNOWN"):
                        event = "BULLISH_MSS"
                        self.trend = "BULLISH"
                    else:
                        event = "BULLISH_BOS"

                    events.append(
                        {
                            "event": event,
                            "time": swing["time"],
                            "price": swing["price"],
                            "trend": self.trend,
                        }
                    )

                previous_high = swing

            elif t in ("HL", "LL"):

                if previous_low is None:
                    previous_low = swing
                    continue

                if swing["price"] < previous_low["price"]:

                    if self.trend in ("BULLISH", "UNKNOWN"):
                        event = "BEARISH_MSS"
                        self.trend = "BEARISH"
                    else:
                        event = "BEARISH_BOS"

                    events.append(
                        {
                            "event": event,
                            "time": swing["time"],
                            "price": swing["price"],
                            "trend": self.trend,
                        }
                    )

                previous_low = swing

        return events
