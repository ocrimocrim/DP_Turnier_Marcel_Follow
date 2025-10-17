import logging
import os
from datetime import datetime

from event_id import get_event_id
from fetch_scorecard import fetch_scorecard
from parser import parse_scorecard
from discord_notify import send_discord_message

# Logging Setup
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"run_{datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def safe_step(step_name, func, *args, **kwargs):
    """Führt einen Schritt aus und fängt alle Fehler ab, damit der Bot stabil bleibt."""
    logging.info(f"🟦 Starte Schritt: {step_name}")
    try:
        result = func(*args, **kwargs)
        logging.info(f"✅ Schritt erfolgreich: {step_name}")
        return result
    except Exception as e:
        logging.exception(f"❌ Fehler in Schritt {step_name}: {e}")
        return None


def main():
    logging.info("🚀 Starte DPWT Marcel Bot – Debug Modus aktiviert")
    logging.info(f"Aktuelles Datum: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

    # Schritt 1 – Turnier/Event finden
    event_id = safe_step("Event-ID ermitteln", get_event_id)
    if not event_id:
        logging.warning("Event-ID konnte nicht ermittelt werden. Bot beendet sich kontrolliert.")
        return

    # Schritt 2 – Scorecard abrufen
    raw_path = safe_step("Scorecard abrufen", fetch_scorecard, event_id=event_id)
    if not raw_path or not os.path.exists(raw_path):
        logging.warning("Scorecard-Datei fehlt oder konnte nicht geladen werden.")
        return

    # Schritt 3 – Scorecard parsen
    parsed_path = safe_step("Scorecard parsen", parse_scorecard, raw_path)
    if not parsed_path or not os.path.exists(parsed_path):
        logging.warning("Parsing-Ergebnis fehlt. Runde wird übersprungen.")
        return

    # Schritt 4 – Discord Nachricht senden
    sent = safe_step("Discord-Nachricht senden", send_discord_message, parsed_path)
    if sent is None:
        logging.warning("Discord-Versand übersprungen oder fehlgeschlagen.")

    logging.info("🏁 Bot-Lauf abgeschlossen – alle Module verarbeitet.")


if __name__ == "__main__":
    main()