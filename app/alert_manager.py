import json
import os

from app.telegram_alert import TelegramAlert


STATE_FILE = os.path.join(
    os.path.dirname(__file__),
    "alert_state.json",
)


class AlertManager:
    def __init__(self):
        self.telegram = TelegramAlert()
        self.last_setup_id = self._load_last_setup_id()

    def _load_last_setup_id(self):
        if not os.path.exists(STATE_FILE):
            return None

        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)

            return data.get("last_setup_id")

        except (OSError, json.JSONDecodeError):
            print("⚠️ Could not read alert state")
            return None

    def _save_last_setup_id(self, setup_id):
        temp_file = STATE_FILE + ".tmp"

        with open(temp_file, "w") as f:
            json.dump(
                {"last_setup_id": setup_id},
                f,
                indent=2,
            )

        os.replace(temp_file, STATE_FILE)

    def send_new_setup(self, setup_id: str, message: str) -> bool:
        if setup_id == self.last_setup_id:
            print("⏭️ Duplicate setup — alert skipped")
            return False

        sent = self.telegram.send(message)

        if sent:
            self.last_setup_id = setup_id
            self._save_last_setup_id(setup_id)
            print("✅ New setup alert sent")
            print(f"💾 Setup state saved: {setup_id[:12]}...")

        return sent
