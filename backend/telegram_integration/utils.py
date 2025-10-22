import os
import requests
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def bot_send_message(telegram_id: str, message: str):
    "Sends a message to a telegram user."

    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN in environment variables")
    

    if not telegram_id:
        raise ValueError("telegram_id is required")

    if not message:
        raise ValueError("message cannot be empty")
    
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": telegram_id, "text": message}
    response = requests.post(url, data=payload)

    try:
        result = response.json()
    except Exception:
        result = {"status": "error", "message": "Invalid JSON response from Telegram"}

    return result