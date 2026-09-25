from dataclasses import dataclass


@dataclass
class Mitigation:
    index: int
    time: object
    direction: str
    zone_type: str
    top: float
    bottom: float


class MitigationDetector:

    def detect(self, candles, zones):

        mitigations = []

        for zone in zones:

            touched = False

            for i in range(zone.index + 1, len(candles)):

                candle = candles[i]

                # Price entered the zone
                if (
                    candle.high >= zone.bottom
                    and candle.low <= zone.top
                ):

                    mitigations.append(
                        Mitigation(
                            index=i,
                            time=candle.time,
                            direction=zone.direction,
                            zone_type=type(zone).__name__,
                            top=round(zone.top, 2),
                            bottom=round(zone.bottom, 2),
                        )
                    )

                    touched = True
                    break

            if not touched:
                continue

        return mitigations
