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


def _build_message(risk_level, disaster, location, risk_score):
    """Build the exact alert message for each risk level."""
    key = risk_level.lower()
    disaster_label = disaster.capitalize()

    if key == 'high':
        _DISASTER_EMOJI = {
            'flood': '🌊', 'earthquake': '🏚️', 'landslide': '⛰️',
            'cyclone': '🌀', 'drought': '☀️',
        }
        d_emoji = _DISASTER_EMOJI.get(disaster.lower(), '🌪️')
        return (
            f"🚨 HIGH RISK ALERT — IMMEDIATE ACTION REQUIRED!\n\n"
            f"⚠️ A high-risk disaster situation has been detected.\n\n"
            f"📍 Location: {location}\n"
            f"{d_emoji} Disaster Type: {disaster_label}\n"
            f"🔴 Risk Level: HIGH\n"
            f"📊 Risk Score: {risk_score:.1f}%\n\n"
            f"🛑 Safety Instructions:\n"
            f"• Move to a safe location immediately.\n"
            f"• Stay away from floodwater, damaged buildings, and hazardous areas.\n"
            f"• Follow instructions from local authorities.\n"
            f"• Contact emergency services if necessary.\n\n"
            f"⚡ Please act immediately and share this alert with people in the affected area.\n"
            f"Stay safe! 🙏"
        )

    if key == 'medium':
        return (
            f"⚠️ MEDIUM RISK WARNING — STAY ALERT!\n\n"
            f"A potential disaster risk has been detected. Please remain cautious and prepared.\n\n"
            f"📍 Location: {location}\n"
            f"🌦️ Disaster Type: {disaster_label}\n"
            f"🟠 Risk Level: MEDIUM\n"
            f"📊 Risk Score: {risk_score:.1f}%\n\n"
            f"🛡️ Safety Instructions:\n"
            f"• Monitor official weather and disaster updates.\n"
            f"• Keep an emergency kit, food, water, and essential medicines ready.\n"
            f"• Avoid unnecessary travel to potentially affected areas.\n"
            f"• Be prepared to move to a safer location if conditions worsen.\n\n"
            f"🔔 Stay alert and follow official instructions.\n"
            f"Your safety matters! 🙏"
        )

    # low
    return (
        f"✅ LOW RISK NOTIFICATION — STAY INFORMED\n\n"
        f"The system currently indicates a low disaster risk level.\n\n"
        f"📍 Location: {location}\n"
        f"🌤️ Disaster Type: {disaster_label}\n"
        f"🟢 Risk Level: LOW\n"
        f"📊 Risk Score: {risk_score:.1f}%\n\n"
        f"💡 Safety Recommendations:\n"
        f"• Continue your normal activities with reasonable caution.\n"
        f"• Stay informed through official weather and disaster updates.\n"
        f"• Keep basic emergency supplies ready.\n"
        f"• Report any unusual conditions to the appropriate authorities.\n\n"
        f"✅ No immediate action is indicated by this risk assessment. "
        f"Conditions can change, so continue monitoring official alerts.\n"
        f"Stay safe! 🌱"
    )


def send_telegram_alert_by_risk(disaster, risk_level, confidence, timestamp, location='Unknown'):
    """Send a Telegram alert appropriate for the given risk level."""
    key = risk_level.lower()
    if key not in ('high', 'medium', 'low'):
        return False
    message = _build_message(key, disaster, location, confidence)
    # Use a time-bucketed key so each prediction sends its own alert
    # while still preventing duplicate bursts within the same minute
    minute_bucket = time.strftime('%Y%m%d%H%M')
    condition_key = f"{disaster}:{key}:{minute_bucket}"
    return send_telegram_alert(message, condition_key=condition_key)


def reverse_geocode(lat, lon):
    """Return a human-readable place name for the given coordinates using Nominatim."""
    try:
        resp = requests.get(
            'https://nominatim.openstreetmap.org/reverse',
            params={'lat': lat, 'lon': lon, 'format': 'json'},
            headers={'User-Agent': 'PreDisasterPredictor/1.0'},
            timeout=8,
        )
        if resp.status_code == 200:
            addr = resp.json().get('address', {})
            city = addr.get('city') or addr.get('town') or addr.get('village') or addr.get('county')
            district = addr.get('state_district')
            state = addr.get('state')
            country = addr.get('country')
            # Include district name for precise location (e.g. Karnataka districts)
            parts = [p for p in [city, district, state, country] if p and p != city]
            result = ', '.join([city] + parts) if city else ', '.join(p for p in [district, state, country] if p)
            if result:
                return result
    except Exception:
        pass
    return f'{float(lat):.4f}, {float(lon):.4f}'


def send_telegram_test_alert():
    """Send a test Telegram message."""

    message = """🧪 TEST ALERT

Telegram notification system is working correctly.

Pre-Disaster Predictor
"""

    return send_telegram_alert(message)