import os
import logging
import threading
import time

import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
logger = logging.getLogger(__name__)
_cooldown_lock = threading.Lock()
_last_alert_times = {}
_cooldown_seconds = max(0, int(os.getenv("TELEGRAM_ALERT_COOLDOWN_SECONDS", "300")))


def send_telegram_alert(message, *, condition_key=None):
    """Send a message to the configured Telegram chat."""

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram alert skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is missing.")
        return False

    reservation_time = None
    if condition_key and _cooldown_seconds:
        reservation_time = time.monotonic()
        with _cooldown_lock:
            last_sent = _last_alert_times.get(condition_key)
            if last_sent is not None and reservation_time - last_sent < _cooldown_seconds:
                logger.info("Telegram alert suppressed by cooldown for %s.", condition_key)
                return False
            _last_alert_times[condition_key] = reservation_time

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message
            },
            timeout=10
        )

        response.raise_for_status()
        if not response.json().get("ok"):
            raise RuntimeError("Telegram API returned an unsuccessful response.")
    except (requests.RequestException, ValueError, RuntimeError) as error:
        if reservation_time is not None:
            with _cooldown_lock:
                if _last_alert_times.get(condition_key) == reservation_time:
                    _last_alert_times.pop(condition_key, None)
        logger.error("Telegram alert failed: %s", str(error).replace(TELEGRAM_BOT_TOKEN, "[REDACTED]"))
        return False

    if reservation_time is not None:
        with _cooldown_lock:
            _last_alert_times[condition_key] = time.monotonic()
    logger.info("Telegram alert sent successfully.")
    return True


def send_telegram_test_alert():
    """Send a test Telegram message."""

    message = """🧪 TEST ALERT

Telegram notification system is working correctly.

Pre-Disaster Predictor
"""

    return send_telegram_alert(message)