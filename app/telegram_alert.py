import os
import requests


class TelegramAlert:
    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not self.bot_token:
            raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

        if not self.chat_id:
            raise RuntimeError("TELEGRAM_CHAT_ID is not set")

        self.url = (
            f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        )

    def send(self, message: str) -> bool:
        payload = {
            "chat_id": self.chat_id,
            "text": message,
        }

        try:
            response = requests.post(
                self.url,
                json=payload,
                timeout=15,
            )

            data = response.json()

            if response.status_code == 200 and data.get("ok"):
                return True

            print("Telegram API error:", data)
            return False

        except requests.RequestException as exc:
            print("Telegram request failed:", exc)
            return False
