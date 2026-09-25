import json
import os
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv


# ==========================================================
# PATHS / ENVIRONMENT
# ==========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

ENV_FILE = os.path.join(
    BASE_DIR,
    ".env",
)

STATE_FILE = os.path.join(
    BASE_DIR,
    "app",
    "latest_signal.json",
)

load_dotenv(
    ENV_FILE,
    override=True,
)


# ==========================================================
# CONFIG
# ==========================================================

from config.settings import (
    DEFAULT_MARKETS,
    ENTRY_TIMEFRAME,
    CONFIRMATION_TIMEFRAME,
    BIAS_TIMEFRAME,
)


# ==========================================================
# AEGIS TELEGRAM BOT
# ==========================================================

class AegisTelegramBot:

    def __init__(self):

        self.token = os.getenv(
            "TELEGRAM_BOT_TOKEN"
        )

        if not self.token:
            raise RuntimeError(
                "TELEGRAM_BOT_TOKEN is not set"
            )

        self.base_url = (
            f"https://api.telegram.org/bot"
            f"{self.token}"
        )

        self.offset = 0

        print(
            "🤖 AEGIS AI TELEGRAM BOT"
        )

        print(
            "Status: INITIALIZING"
        )

        print()


    # ======================================================
    # TELEGRAM API
    # ======================================================

    def api(
        self,
        method,
        payload=None,
    ):

        url = (
            f"{self.base_url}/{method}"
        )

        response = requests.post(
            url,
            json=payload or {},
            timeout=40,
        )

        data = response.json()

        if not data.get("ok"):

            raise RuntimeError(
                f"Telegram API error: {data}"
            )

        return data


    # ======================================================
    # SEND MESSAGE
    # ======================================================

    def send_message(
        self,
        chat_id,
        text,
        reply_markup=None,
        message_thread_id=None,
    ):

        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        if reply_markup:

            payload[
                "reply_markup"
            ] = reply_markup

        if message_thread_id is not None:

            payload[
                "message_thread_id"
            ] = message_thread_id

        return self.api(
            "sendMessage",
            payload,
        )


    # ======================================================
    # EDIT MESSAGE
    # ======================================================

    def edit_message(
        self,
        chat_id,
        message_id,
        text,
        reply_markup=None,
    ):

        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
        }

        if reply_markup:

            payload[
                "reply_markup"
            ] = reply_markup

        try:

            return self.api(
                "editMessageText",
                payload,
            )

        except RuntimeError as exc:

            if (
                "message is not modified"
                in str(exc).lower()
            ):

                return None

            raise


    # ======================================================
    # CALLBACK ANSWER
    # ======================================================

    def answer_callback(
        self,
        callback_query_id,
    ):

        try:

            return self.api(
                "answerCallbackQuery",
                {
                    "callback_query_id":
                        callback_query_id
                },
            )

        except RuntimeError as exc:

            print(
                "⚠️ Callback answer error:",
                exc,
            )

            return None


    # ======================================================
    # KEYBOARDS
    # ======================================================

    def main_menu(self):

        return {
            "inline_keyboard": [

                [
                    {
                        "text":
                            "📊 Analyze Market",
                        "callback_data":
                            "analyze",
                    }
                ],

                [
                    {
                        "text":
                            "📈 Markets",
                        "callback_data":
                            "markets",
                    },
                    {
                        "text":
                            "📡 Latest Signals",
                        "callback_data":
                            "signals",
                    },
                ],

                [
                    {
                        "text":
                            "⚙️ System Status",
                        "callback_data":
                            "status",
                    },
                    {
                        "text":
                            "❓ Help",
                        "callback_data":
                            "help",
                    },
                ],

                [
                    {
                        "text":
                            "🛡️ About AEGIS",
                        "callback_data":
                            "about",
                    }
                ],

            ]
        }


    def home_menu(self):

        return {
            "inline_keyboard": [

                [
                    {
                        "text":
                            "🏠 Main Menu",
                        "callback_data":
                            "main",
                    }
                ]

            ]
        }


    def signal_menu(self):

        return {
            "inline_keyboard": [

                [
                    {
                        "text":
                            "🔄 Refresh Analysis",
                        "callback_data":
                            "analyze",
                    }
                ],

                [
                    {
                        "text":
                            "🏠 Main Menu",
                        "callback_data":
                            "main",
                    }
                ],

            ]
        }


    # ======================================================
    # STATE FILE
    # ======================================================

    def load_latest_signal(self):

        if not os.path.exists(
            STATE_FILE
        ):

            return None

        try:

            with open(
                STATE_FILE,
                "r",
                encoding="utf-8",
            ) as file:

                data = json.load(
                    file
                )

            signal = data.get(
                "signal"
            )

            if not isinstance(
                signal,
                dict,
            ):

                return None

            result = dict(
                signal
            )

            result[
                "symbol"
            ] = data.get(
                "symbol",
                DEFAULT_MARKETS[0],
            )

            result[
                "timeframe"
            ] = data.get(
                "timeframe",
                ENTRY_TIMEFRAME,
            )

            result[
                "updated_at"
            ] = data.get(
                "updated_at"
            )

            result[
                "setup_id"
            ] = data.get(
                "setup_id"
            )

            result[
                "valid_setup"
            ] = data.get(
                "valid_setup",
                False,
            )

            return result

        except (
            OSError,
            json.JSONDecodeError,
        ) as exc:

            print(
                "⚠️ Could not read latest signal:",
                exc,
            )

            return None


    # ======================================================
    # TIME HELPERS
    # ======================================================

    def state_age_seconds(
        self,
        data,
    ):

        updated_at = data.get(
            "updated_at"
        )

        if not updated_at:

            return None

        try:

            timestamp = (
                datetime.fromisoformat(
                    updated_at.replace(
                        "Z",
                        "+00:00",
                    )
                )
            )

            now = datetime.now(
                timezone.utc
            )

            return max(
                0,
                int(
                    (
                        now - timestamp
                    ).total_seconds()
                ),
            )

        except (
            ValueError,
            TypeError,
        ):

            return None


    def format_age(
        self,
        seconds,
    ):

        if seconds is None:

            return "Unknown"


        if seconds < 60:

            return (
                f"{seconds}s ago"
            )


        minutes = (
            seconds // 60
        )


        if minutes < 60:

            return (
                f"{minutes}m ago"
            )


        hours = (
            minutes // 60
        )


        if hours < 24:

            return (
                f"{hours}h "
                f"{minutes % 60}m ago"
            )


        days = (
            hours // 24
        )


        return (
            f"{days}d "
            f"{hours % 24}h ago"
        )


    # ======================================================
    # MAIN DASHBOARD
    # ======================================================

    def welcome(
        self,
        chat_id,
        message_id=None,
        message_thread_id=None,
    ):

        text = """🛡️ AEGIS AI

━━━━━━━━━━━━━━━━━━━━
MARKET INTELLIGENCE
━━━━━━━━━━━━━━━━━━━━

🧠 Multi-Timeframe Analysis
H1 → M15 → M5

📡 Live market monitoring
⚡ Structured price-action engine
🛡️ Risk validation
📊 Signal intelligence

Choose an option below to access AEGIS AI.

⚠️ Educational and informational purposes only."""

        if message_id:

            self.edit_message(
                chat_id,
                message_id,
                text,
                self.main_menu(),
            )

        else:

            self.send_message(
                chat_id,
                text,
                self.main_menu(),
                message_thread_id,
            )


    # ======================================================
    # MARKETS
    # ======================================================

    def markets(
        self,
        chat_id,
        message_id=None,
        message_thread_id=None,
    ):

        markets = "\n".join(
            f"• {market}"
            for market in DEFAULT_MARKETS
        )

        text = f"""📈 AEGIS AI MARKETS

━━━━━━━━━━━━━━━━━━━━
CONFIGURED MARKETS
━━━━━━━━━━━━━━━━━━━━

{markets}

TIMEFRAME STRUCTURE

H1  → Higher-Timeframe Bias
M15 → Confirmation
M5  → Execution

The watcher maintains the market data cache and publishes the latest analysis state to the Telegram interface."""

        if message_id:

            self.edit_message(
                chat_id,
                message_id,
                text,
                self.home_menu(),
            )

        else:

            self.send_message(
                chat_id,
                text,
                self.home_menu(),
                message_thread_id,
            )


    # ======================================================
    # SYSTEM STATUS
    # ======================================================

    def status(
        self,
        chat_id,
        message_id=None,
        message_thread_id=None,
    ):

        signal = (
            self.load_latest_signal()
        )

        state_exists = os.path.exists(
            STATE_FILE
        )

        if (
            state_exists
            and signal
        ):

            watcher_status = (
                "🟢 ONLINE"
            )

            last_update = (
                self.format_age(
                    self.state_age_seconds(
                        signal
                    )
                )
            )

        else:

            watcher_status = (
                "🔴 NO STATE"
            )

            last_update = (
                "No analysis available"
            )


        text = f"""⚙️ AEGIS AI SYSTEM STATUS

━━━━━━━━━━━━━━━━━━━━
SYSTEM HEALTH
━━━━━━━━━━━━━━━━━━━━

Telegram Interface
🟢 ONLINE

Watcher State
{watcher_status}

Analysis Engine
🟢 CONNECTED

MTF Engine
🟢 H1 → M15 → M5

Shared Market State
{"🟢 AVAILABLE" if signal else "🔴 UNAVAILABLE"}

Last Analysis
{last_update}

━━━━━━━━━━━━━━━━━━━━
ARCHITECTURE
━━━━━━━━━━━━━━━━━━━━

Twelve Data
     ↓
AEGIS Watcher
     ↓
Analysis Pipeline
     ↓
latest_signal.json
     ↓
Telegram Dashboard

Telegram does not request fresh candles directly."""

        if message_id:

            self.edit_message(
                chat_id,
                message_id,
                text,
                self.home_menu(),
            )

        else:

            self.send_message(
                chat_id,
                text,
                self.home_menu(),
                message_thread_id,
            )


    # ======================================================
    # ABOUT
    # ======================================================

    def about(
        self,
        chat_id,
        message_id=None,
        message_thread_id=None,
    ):

        text = """🛡️ ABOUT AEGIS AI

━━━━━━━━━━━━━━━━━━━━
MULTI-TIMEFRAME INTELLIGENCE
━━━━━━━━━━━━━━━━━━━━

AEGIS AI analyzes market structure through:

H1
Higher-Timeframe Bias
        ↓
M15
Confirmation
        ↓
M5
Execution

The engine evaluates:

• Market Structure
• Liquidity
• Displacement
• Fair Value Gaps
• Breaker Blocks
• Institutional Order Blocks
• Premium / Discount
• Entry Conditions
• Risk / Reward
• Trade Validation

AEGIS is designed for systematic market analysis.

⚠️ It does not guarantee profitable trades."""

        if message_id:

            self.edit_message(
                chat_id,
                message_id,
                text,
                self.home_menu(),
            )

        else:

            self.send_message(
                chat_id,
                text,
                self.home_menu(),
                message_thread_id,
            )


    # ======================================================
    # HELP
    # ======================================================

    def help(
        self,
        chat_id,
        message_id=None,
        message_thread_id=None,
    ):

        text = """❓ AEGIS AI HELP

📊 Analyze Market
View the latest analysis produced by the live AEGIS watcher.

📡 Latest Signals
View the latest stored market signal.

📈 Markets
View configured instruments and timeframes.

⚙️ System Status
Check the current AEGIS system state.

🛡️ About AEGIS
Learn how the analysis engine works.

COMMANDS

/start
Open the main dashboard.

/analyze
View latest market analysis.

/signals
View latest signal.

/markets
View configured markets.

/status
View system status.

/help
Show this help page.

/about
Learn about AEGIS AI."""

        if message_id:

            self.edit_message(
                chat_id,
                message_id,
                text,
                self.home_menu(),
            )

        else:

            self.send_message(
                chat_id,
                text,
                self.home_menu(),
                message_thread_id,
            )


    # ======================================================
    # VALUE HELPER
    # ======================================================

    def get_value(
        self,
        signal,
        name,
        default=None,
    ):

        if isinstance(
            signal,
            dict,
        ):

            return signal.get(
                name,
                default,
            )

        return getattr(
            signal,
            name,
            default,
        )


    # ======================================================
    # SIGNAL FORMAT
    # ======================================================

    def format_signal(
        self,
        signal,
        market,
    ):

        direction = str(
            self.get_value(
                signal,
                "direction",
                "N/A",
            )
        ).upper()

        confidence = (
            self.get_value(
                signal,
                "confidence",
                "N/A",
            )
        )

        entry = (
            self.get_value(
                signal,
                "entry",
                "N/A",
            )
        )

        sl = (
            self.get_value(
                signal,
                "sl",
                self.get_value(
                    signal,
                    "stop_loss",
                    "N/A",
                ),
            )
        )

        tp1 = (
            self.get_value(
                signal,
                "tp1",
                "N/A",
            )
        )

        tp2 = (
            self.get_value(
                signal,
                "tp2",
                "N/A",
            )
        )

        rr = (
            self.get_value(
                signal,
                "risk_reward",
                "N/A",
            )
        )

        setup_type = (
            self.get_value(
                signal,
                "setup_type",
                "N/A",
            )
        )

        entry_zone = (
            self.get_value(
                signal,
                "entry_zone",
                "N/A",
            )
        )

        mtf_status = (
            self.get_value(
                signal,
                "mtf_status",
                "N/A",
            )
        )

        execution_type = (
            self.get_value(
                signal,
                "execution_type",
                "N/A",
            )
        )

        risk_mode = (
            self.get_value(
                signal,
                "risk_mode",
                "N/A",
            )
        )

        trade_valid = (
            self.get_value(
                signal,
                "trade_valid",
                False,
            )
        )

        setup_status = (
            self.get_value(
                signal,
                "setup_status",
                "N/A",
            )
        )

        reasons = (
            self.get_value(
                signal,
                "reasons",
                [],
            )
        )

        validation_reasons = (
            self.get_value(
                signal,
                "validation_reasons",
                [],
            )
        )


        if isinstance(
            reasons,
            str,
        ):

            reasons_text = (
                f"• {reasons}"
            )

        elif reasons:

            reasons_text = "\n".join(
                f"• {reason}"
                for reason in reasons
            )

        else:

            reasons_text = (
                "• No reasons provided"
            )


        if isinstance(
            validation_reasons,
            str,
        ):

            validation_text = (
                f"• {validation_reasons}"
            )

        elif validation_reasons:

            validation_text = "\n".join(
                f"• {reason}"
                for reason in validation_reasons
            )

        else:

            validation_text = (
                "• No validation details"
            )


        if direction == "BULLISH":

            direction_display = (
                "🟢 BULLISH"
            )

        elif direction == "BEARISH":

            direction_display = (
                "🔴 BEARISH"
            )

        else:

            direction_display = (
                f"⚪ {direction}"
            )


        status_display = (
            "🟢 VALID"
            if trade_valid
            else "🔴 INVALID"
        )


        age = self.format_age(
            self.state_age_seconds(
                signal
            )
        )


        return f"""📊 AEGIS AI MARKET ANALYSIS

━━━━━━━━━━━━━━━━━━━━
{market} • {ENTRY_TIMEFRAME}
━━━━━━━━━━━━━━━━━━━━

Direction
{direction_display}

Confidence
{confidence}

Setup
{setup_type}

Entry Zone
{entry_zone}

━━━━━━━━━━━━━━━━━━━━
TRADE LEVELS
━━━━━━━━━━━━━━━━━━━━

Entry: {entry}
Stop Loss: {sl}

TP1: {tp1}
TP2: {tp2}

Risk/Reward: {rr}

━━━━━━━━━━━━━━━━━━━━
MTF DECISION
━━━━━━━━━━━━━━━━━━━━

MTF Status: {mtf_status}
Execution: {execution_type}
Risk Mode: {risk_mode}

Setup Status: {setup_status}
Trade Validation: {status_display}

━━━━━━━━━━━━━━━━━━━━
REASONS
━━━━━━━━━━━━━━━━━━━━

{reasons_text}

Validation
{validation_text}

━━━━━━━━━━━━━━━━━━━━

Last Updated: {age}

⚠️ Informational market analysis only."""


    # ======================================================
    # ANALYZE
    # ======================================================

    def analyze(
        self,
        chat_id,
        message_id=None,
        message_thread_id=None,
    ):

        signal = (
            self.load_latest_signal()
        )

        if not signal:

            text = """📊 AEGIS AI MARKET ANALYSIS

⚪ No analysis is currently available.

The AEGIS watcher has not published a market state yet.

Expected state file:

app/latest_signal.json"""

            if message_id:

                self.edit_message(
                    chat_id,
                    message_id,
                    text,
                    self.home_menu(),
                )

            else:

                self.send_message(
                    chat_id,
                    text,
                    self.home_menu(),
                    message_thread_id,
                )

            return


        market = signal.get(
            "symbol",
            DEFAULT_MARKETS[0],
        )

        text = (
            self.format_signal(
                signal,
                market,
            )
        )


        if message_id:

            self.edit_message(
                chat_id,
                message_id,
                text,
                self.signal_menu(),
            )

        else:

            self.send_message(
                chat_id,
                text,
                self.signal_menu(),
                message_thread_id,
            )


    # ======================================================
    # LATEST SIGNALS
    # ======================================================

    def signals(
        self,
        chat_id,
        message_id=None,
        message_thread_id=None,
    ):

        signal = (
            self.load_latest_signal()
        )

        if not signal:

            text = """📡 AEGIS AI LATEST SIGNAL

⚪ No signal state is currently available.

The watcher has not published:

app/latest_signal.json"""

        else:

            market = signal.get(
                "symbol",
                DEFAULT_MARKETS[0],
            )

            direction = str(
                signal.get(
                    "direction",
                    "N/A",
                )
            ).upper()

            confidence = signal.get(
                "confidence",
                "N/A",
            )

            entry = signal.get(
                "entry",
                "N/A",
            )

            sl = signal.get(
                "sl",
                "N/A",
            )

            tp1 = signal.get(
                "tp1",
                "N/A",
            )

            tp2 = signal.get(
                "tp2",
                "N/A",
            )

            rr = signal.get(
                "risk_reward",
                "N/A",
            )

            setup_status = signal.get(
                "setup_status",
                "N/A",
            )

            mtf_status = signal.get(
                "mtf_status",
                "N/A",
            )

            age = self.format_age(
                self.state_age_seconds(
                    signal
                )
            )


            if direction == "BULLISH":

                emoji = "🟢"

            elif direction == "BEARISH":

                emoji = "🔴"

            else:

                emoji = "⚪"


            text = f"""📡 AEGIS AI LATEST SIGNAL

━━━━━━━━━━━━━━━━━━━━
{market}
━━━━━━━━━━━━━━━━━━━━

Direction
{emoji} {direction}

Status
{setup_status}

Confidence
{confidence}

Entry
{entry}

Stop Loss
{sl}

TP1
{tp1}

TP2
{tp2}

Risk/Reward
{rr}

MTF Status
{mtf_status}

Updated
{age}

Use 📊 Analyze Market for the complete analysis."""


        if message_id:

            self.edit_message(
                chat_id,
                message_id,
                text,
                self.home_menu(),
            )

        else:

            self.send_message(
                chat_id,
                text,
                self.home_menu(),
                message_thread_id,
            )


    # ======================================================
    # CALLBACK HANDLER
    # ======================================================

    def handle_callback(
        self,
        callback,
    ):

        callback_id = callback.get(
            "id"
        )

        data = callback.get(
            "data"
        )

        message = callback.get(
            "message"
        )

        if not message:

            if callback_id:

                self.answer_callback(
                    callback_id
                )

            return


        chat = message.get(
            "chat",
            {},
        )

        chat_id = chat.get(
            "id"
        )

        message_id = message.get(
            "message_id"
        )


        if callback_id:

            self.answer_callback(
                callback_id
            )


        if data == "main":

            self.welcome(
                chat_id,
                message_id,
            )

        elif data == "analyze":

            self.analyze(
                chat_id,
                message_id,
            )

        elif data == "markets":

            self.markets(
                chat_id,
                message_id,
            )

        elif data == "signals":

            self.signals(
                chat_id,
                message_id,
            )

        elif data == "status":

            self.status(
                chat_id,
                message_id,
            )

        elif data == "help":

            self.help(
                chat_id,
                message_id,
            )

        elif data == "about":

            self.about(
                chat_id,
                message_id,
            )


    # ======================================================
    # MESSAGE HANDLER
    # ======================================================

    def handle_message(
        self,
        message,
    ):

        chat = message.get(
            "chat",
            {},
        )

        chat_id = chat.get(
            "id"
        )

        message_thread_id = (
            message.get(
                "message_thread_id"
            )
        )

        text = message.get(
            "text",
            "",
        )

        if not text:

            return


        command = (
            text.split()[0]
            .lower()
        )


        if command == "/start":

            self.welcome(
                chat_id,
                message_thread_id=(
                    message_thread_id
                ),
            )

        elif command == "/analyze":

            self.analyze(
                chat_id,
                message_thread_id=(
                    message_thread_id
                ),
            )

        elif command == "/markets":

            self.markets(
                chat_id,
                message_thread_id=(
                    message_thread_id
                ),
            )

        elif command == "/signals":

            self.signals(
                chat_id,
                message_thread_id=(
                    message_thread_id
                ),
            )

        elif command == "/status":

            self.status(
                chat_id,
                message_thread_id=(
                    message_thread_id
                ),
            )

        elif command == "/help":

            self.help(
                chat_id,
                message_thread_id=(
                    message_thread_id
                ),
            )

        elif command == "/about":

            self.about(
                chat_id,
                message_thread_id=(
                    message_thread_id
                ),
            )

        else:

            self.send_message(
                chat_id,
                "🛡️ AEGIS AI\n\n"
                "Use /start to open "
                "the main dashboard.",
                self.main_menu(),
                message_thread_id,
            )


    # ======================================================
    # UPDATE HANDLER
    # ======================================================

    def handle_update(
        self,
        update,
    ):

        callback = update.get(
            "callback_query"
        )

        if callback:

            self.handle_callback(
                callback
            )

            return


        message = update.get(
            "message"
        )

        if message:

            self.handle_message(
                message
            )


    # ======================================================
    # POLLING
    # ======================================================

    def poll(self):

        print(
            "🟢 Telegram bot is running"
        )

        print(
            "Waiting for Telegram updates..."
        )

        print()


        while True:

            try:

                payload = {
                    "offset":
                        self.offset,

                    "timeout":
                        30,

                    "allowed_updates": [
                        "message",
                        "callback_query",
                    ],
                }


                data = self.api(
                    "getUpdates",
                    payload,
                )


                updates = data.get(
                    "result",
                    [],
                )


                for update in updates:

                    self.offset = (
                        update[
                            "update_id"
                        ] + 1
                    )


                    try:

                        self.handle_update(
                            update
                        )

                    except Exception as exc:

                        print(
                            "❌ Update handling error:",
                            exc,
                        )


            except KeyboardInterrupt:

                print()

                print(
                    "🛑 AEGIS AI TELEGRAM BOT STOPPED"
                )

                break


            except Exception as exc:

                print(
                    "❌ Telegram polling error:",
                    exc,
                )

                time.sleep(5)


# ==========================================================
# ENTRY POINT
# ==========================================================

def main():

    bot = (
        AegisTelegramBot()
    )

    bot.poll()


if __name__ == "__main__":

    main()
