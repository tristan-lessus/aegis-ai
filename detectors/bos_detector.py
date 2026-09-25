from dataclasses import dataclass


@dataclass
class StructureEvent:
    time: object
    event: str      # BOS or CHOCH
    direction: str  # BULLISH or BEARISH
    price: float


class BOSDetector:

    def detect(self, classified_swings):

        if len(classified_swings) < 2:
            return []

        events = []
        trend = None

        for swing in classified_swings:

            label = swing["label"]

            # Determine initial trend
            if trend is None:

                if label in ("HH", "HL"):
                    trend = "BULLISH"

                elif label in ("LH", "LL"):
                    trend = "BEARISH"

                continue

            # Bullish Market
            if trend == "BULLISH":

                if label == "HH":

                    events.append(
                        StructureEvent(
                            time=swing["time"],
                            event="BOS",
                            direction="BULLISH",
                            price=swing["price"],
                        )
                    )

                elif label == "LL":

                    trend = "BEARISH"

                    events.append(
                        StructureEvent(
                            time=swing["time"],
                            event="CHOCH",
                            direction="BEARISH",
                            price=swing["price"],
                        )
                    )

            # Bearish Market
            else:

                if label == "LL":

                    events.append(
                        StructureEvent(
                            time=swing["time"],
                            event="BOS",
                            direction="BEARISH",
                            price=swing["price"],
                        )
                    )

                elif label == "HH":

                    trend = "BULLISH"

                    events.append(
                        StructureEvent(
                            time=swing["time"],
                            event="CHOCH",
                            direction="BULLISH",
                            price=swing["price"],
                        )
                    )

        return events
