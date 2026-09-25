import hashlib
import json
import os
import time
from datetime import datetime, timezone

from feeds.provider_factory import ProviderFactory
from engine.analysis_pipeline import AnalysisPipeline
from app.alert_manager import AlertManager


SYMBOL = "XAU/USD"

CANDLE_LIMIT = 300

CHECK_INTERVAL_SECONDS = 60

REFRESH_INTERVALS = {
    "H1": 60 * 60,
    "M15": 15 * 60,
    "M5": 5 * 60,
}

STATE_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "latest_signal.json",
)

MARKET_DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "market_data.json",
)


class AegisWatcher:
    def __init__(self):
        self.provider = ProviderFactory.create("live")
        self.pipeline = AnalysisPipeline()
        self.alert_manager = AlertManager()

        self.cache = {}
        self.last_refresh = {}

        print("🤖 AEGIS AI WATCHER")
        print(f"Symbol: {SYMBOL}")
        print("Mode: RATE-LIMIT SAFE")
        print()

    # ==========================================================
    # CANDLE CACHE
    # ==========================================================

    def _is_stale(self, timeframe):
        now = time.time()
        last = self.last_refresh.get(timeframe, 0)

        return (
            now - last
        ) >= REFRESH_INTERVALS[timeframe]

    def _refresh(self, timeframe):
        print(f"📡 Refreshing {timeframe}...")

        candles = self.provider.get_candles(
            SYMBOL,
            timeframe,
            CANDLE_LIMIT,
        )

        if not candles:
            raise RuntimeError(
                f"No candles returned for {timeframe}"
            )

        self.cache[timeframe] = candles
        self.last_refresh[timeframe] = time.time()

        print(
            f"✅ {timeframe}: "
            f"{len(candles)} candles"
        )

        return candles

    def _get_candles(self, timeframe):
        if (
            timeframe not in self.cache
            or self._is_stale(timeframe)
        ):
            return self._refresh(timeframe)

        return self.cache[timeframe]

    def _save_market_data(self):
        """
        Persist the watcher's already-fetched candle cache.

        The dashboard reads this file instead of requesting
        market data directly from Twelve Data.
        """

        payload = {
            "symbol": SYMBOL,
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "timeframes": {},
        }

        for timeframe in ("H1", "M15", "M5"):
            candles = self.cache.get(timeframe, [])

            payload["timeframes"][timeframe] = [
                {
                    "time": candle.time.isoformat()
                    if hasattr(candle.time, "isoformat")
                    else str(candle.time),
                    "open": candle.open,
                    "high": candle.high,
                    "low": candle.low,
                    "close": candle.close,
                    "volume": candle.volume,
                }
                for candle in candles
            ]

        temp_file = MARKET_DATA_FILE + ".tmp"

        try:
            with open(
                temp_file,
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(
                    payload,
                    f,
                    indent=2,
                )

            os.replace(
                temp_file,
                MARKET_DATA_FILE,
            )

            print(
                "💾 Market candle state saved"
            )

        except OSError as exc:
            print(
                "⚠️ Could not save market data:",
                exc,
            )

    # ==========================================================
    # SIGNAL HELPERS
    # ==========================================================

    @staticmethod
    def _get_value(
        signal,
        name,
        default=None,
    ):
        if isinstance(signal, dict):
            return signal.get(name, default)

        return getattr(
            signal,
            name,
            default,
        )

    def _is_valid_setup(self, signal):
        trade_valid = self._get_value(
            signal,
            "trade_valid",
            False,
        )

        setup_status = self._get_value(
            signal,
            "setup_status",
            "",
        )

        return (
            trade_valid is True
            and str(setup_status).upper() == "VALID"
        )

    def _setup_id(self, signal):
        fields = {
            "symbol": SYMBOL,
            "direction": self._get_value(
                signal,
                "direction",
            ),
            "entry": self._get_value(
                signal,
                "entry",
            ),
            "sl": self._get_value(
                signal,
                "sl",
            ),
            "tp1": self._get_value(
                signal,
                "tp1",
            ),
            "tp2": self._get_value(
                signal,
                "tp2",
            ),
            "setup_type": self._get_value(
                signal,
                "setup_type",
            ),
            "entry_zone": self._get_value(
                signal,
                "entry_zone",
            ),
            "source_time": self._get_value(
                signal,
                "entry_source_time",
            ),
        }

        raw = repr(
            sorted(fields.items())
        )

        return hashlib.sha256(
            raw.encode()
        ).hexdigest()

    # ==========================================================
    # SIGNAL SERIALIZATION
    # ==========================================================

    def _serialize_value(self, value):
        """
        Convert AEGIS detector output into JSON-safe data.

        Detectors may return dictionaries, lists, tuples,
        datetimes, dataclasses, or normal Python objects.
        """

        if value is None:
            return None

        if isinstance(
            value,
            (str, int, float, bool),
        ):
            return value

        if isinstance(
            value,
            (datetime, ),
        ):
            return value.isoformat()

        if isinstance(
            value,
            (list, tuple),
        ):
            return [
                self._serialize_value(item)
                for item in value
            ]

        if isinstance(value, dict):
            return {
                str(key): self._serialize_value(item)
                for key, item in value.items()
            }

        if hasattr(value, "__dict__"):
            return {
                str(key): self._serialize_value(item)
                for key, item in vars(value).items()
                if not str(key).startswith("_")
            }

        return str(value)

    def _serialize_signal(self, signal):
        """
        Serialize the complete AEGIS signal.

        The dashboard needs access to the actual detector
        outputs already attached by AnalysisPipeline.
        """

        fields = [
            "direction",
            "confidence",
            "reasons",
            "entry",
            "sl",
            "tp1",
            "tp2",
            "risk_reward",
            "entry_zone",
            "setup_type",
            "entry_source_time",
            "trade_valid",
            "validation_reasons",
            "setup_status",
            "mtf_status",
            "execution_type",
            "risk_mode",

            # ==================================================
            # AEGIS MARKET / DETECTOR DATA
            # ==================================================
            "current_price",
            "support_resistance",
            "nearest_support",
            "nearest_resistance",
            "swing_high",
            "swing_low",

            "market_swings",
            "market_breaks",

            "liquidity_events",

            "fvg_events",
            "all_fvg_events",

            "breaker_blocks",
            "order_blocks",

            # ==================================================
            # MULTI-TIMEFRAME STRUCTURE
            # ==================================================
            "mtf_context",
            "h1_structure",
            "h1_structure_events",
            "h1_bias",
            "m15_structure",
            "m15_structure_events",
            "m15_bias",
            "mtf_alignment",
        ]

        result = {}

        for field in fields:
            value = self._get_value(
                signal,
                field,
                None,
            )

            if value is None:
                continue

            result[field] = self._serialize_value(
                value
            )

        return result

    def _save_latest_signal(
        self,
        signal,
        setup_id=None,
    ):
        payload = {
            "symbol": SYMBOL,
            "timeframe": "M5",
            "updated_at": datetime.now(
                timezone.utc
            ).isoformat(),
            "setup_id": setup_id,
            "valid_setup": self._is_valid_setup(
                signal
            ),
            "signal": self._serialize_signal(
                signal
            ),
        }

        temp_file = STATE_FILE + ".tmp"

        try:
            with open(
                temp_file,
                "w",
                encoding="utf-8",
            ) as f:
                json.dump(
                    payload,
                    f,
                    indent=2,
                    default=str,
                )

            os.replace(
                temp_file,
                STATE_FILE,
            )

            print(
                "💾 Latest signal state saved"
            )

        except OSError as exc:
            print(
                "⚠️ Could not save signal state:",
                exc,
            )

    # ==========================================================
    # ALERT FORMAT
    # ==========================================================

    def _format_alert(self, signal):
        direction = str(
            self._get_value(
                signal,
                "direction",
                "UNKNOWN",
            )
        ).upper()

        emoji = (
            "🟢"
            if direction == "BULLISH"
            else "🔴"
        )

        entry = self._get_value(
            signal,
            "entry",
            "N/A",
        )

        sl = self._get_value(
            signal,
            "sl",
            "N/A",
        )

        tp1 = self._get_value(
            signal,
            "tp1",
            "N/A",
        )

        tp2 = self._get_value(
            signal,
            "tp2",
            "N/A",
        )

        rr = self._get_value(
            signal,
            "risk_reward",
            "N/A",
        )

        mtf_status = self._get_value(
            signal,
            "mtf_status",
            "N/A",
        )

        execution_type = self._get_value(
            signal,
            "execution_type",
            "N/A",
        )

        risk_mode = self._get_value(
            signal,
            "risk_mode",
            "N/A",
        )

        confidence = self._get_value(
            signal,
            "confidence",
            "N/A",
        )

        setup_type = self._get_value(
            signal,
            "setup_type",
            "N/A",
        )

        entry_zone = self._get_value(
            signal,
            "entry_zone",
            "N/A",
        )

        reasons = self._get_value(
            signal,
            "reasons",
            [],
        )

        if isinstance(
            reasons,
            (list, tuple),
        ):
            reason_text = "\n".join(
                f"• {reason}"
                for reason in reasons
            )
        else:
            reason_text = str(reasons)

        return f"""🤖 AEGIS AI — NEW SETUP

Symbol: {SYMBOL}
Timeframe: M5

Direction: {emoji} {direction}
Setup: {setup_type}
Entry Zone: {entry_zone}
Status: VALID

Entry: {entry}
Stop Loss: {sl}
TP1: {tp1}
TP2: {tp2}

Risk/Reward: {rr}
Confidence: {confidence}

MTF Status: {mtf_status}
Execution: {execution_type}
Risk Mode: {risk_mode}

Reasons:
{reason_text}

🕐 {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
"""

    # ==========================================================
    # ANALYSIS
    # ==========================================================

    def analyze(self):
        h1 = self._get_candles("H1")
        m15 = self._get_candles("M15")
        m5 = self._get_candles("M5")

        self._save_market_data()

        print("🧠 Running Aegis pipeline...")

        signal = self.pipeline.analyze(
            m5,
            m15_candles=m15,
            h1_candles=h1,
        )

        return signal

    # ==========================================================
    # SINGLE WATCH CYCLE
    # ==========================================================

    def run_once(self):
        try:
            signal = self.analyze()

            valid = self._is_valid_setup(
                signal
            )

            setup_id = None

            if valid:
                setup_id = self._setup_id(
                    signal
                )

            self._save_latest_signal(
                signal,
                setup_id,
            )

            if not valid:
                print(
                    "⚪ No valid setup"
                )
                return

            print(
                "🟢 VALID setup detected"
            )

            print(
                f"Setup ID: "
                f"{setup_id[:12]}..."
            )

            message = self._format_alert(
                signal
            )

            self.alert_manager.send_new_setup(
                setup_id,
                message,
            )

        except Exception as exc:
            print(
                f"❌ Watcher error: {exc}"
            )

    # ==========================================================
    # WATCH LOOP
    # ==========================================================

    def run(self):
        print("🚀 Watcher started")

        print(
            f"⏱️ Checking every "
            f"{CHECK_INTERVAL_SECONDS} seconds"
        )

        print()

        while True:
            started = time.time()

            self.run_once()

            elapsed = (
                time.time() - started
            )

            sleep_for = max(
                1,
                CHECK_INTERVAL_SECONDS
                - elapsed,
            )

            print(
                f"💤 Next check in "
                f"{int(sleep_for)} seconds..."
            )

            print()

            time.sleep(
                sleep_for
            )


if __name__ == "__main__":
    watcher = AegisWatcher()
    watcher.run()
