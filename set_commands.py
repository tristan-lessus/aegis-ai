import os
import requests
from dotenv import load_dotenv

load_dotenv(".env", override=True)

token = os.getenv("TELEGRAM_BOT_TOKEN")

if not token:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

url = f"https://api.telegram.org/bot{token}/setMyCommands"

commands = [
    {
        "command": "start",
        "description": "Open AEGIS AI",
    },
    {
        "command": "analyze",
        "description": "Analyze the current market",
    },
    {
        "command": "markets",
        "description": "View available markets",
    },
    {
        "command": "signals",
        "description": "View latest signals",
    },
    {
        "command": "status",
        "description": "Check AEGIS AI status",
    },
    {
        "command": "help",
        "description": "Show available commands",
    },
    {
        "command": "about",
        "description": "Learn about AEGIS AI",
    },
]

response = requests.post(
    url,
    json={"commands": commands},
    timeout=15,
)

data = response.json()

if data.get("ok"):
    print("✅ AEGIS AI commands registered successfully")
else:
    print("❌ Telegram API error")
    print(data)
