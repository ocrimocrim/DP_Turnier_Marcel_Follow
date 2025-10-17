# main.py
import logging
import sys
from datetime import datetime

from event_id import extract_event_id
from fetch_scorecard import fetch_scorecard
from parser import parse_scorecard
from discord_notify import send_discord_message

# --------------------------------------------------------------------
# Logging Setup
# --------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

# --------------------------------------------------------------------
# Konstanten
# --------------------------------------------------------------------
TOURNAMENT_BASE = "https://www.europeantour.com/dpworld-tour"
MARCEL_SLUG = "/dp-world-india-championship-2025"
PLAYER_ID = 35703

# --------------------------------------------------------------------
# Hauptlogik
# --------------------------------------------------------------------
def main():
    logging.info("Starte DPWT Marcel Follow Bot")

    event_page_url = f"{TOURNAMENT_BASE}{MARCEL_SLUG}"
    logging.info(f"Turnierseite: {event_page_url}")

    # EventId finden
    event_id = extract_event_id(event_page_url)
    if not event_id:
        logging.error("EventId wurde nicht gefunden. Abbruch.")
        return
    logging.info(f"EventId erkannt: {event_id}")

    # Scorecard abrufen
    scorecard_path = fetch_scorecard(event_id)
    if not scorecard_path:
        logging.error("Scorecard konnte nicht abgerufen werden. Abbruch.")
        return

    # Scorecard parsen
    parsed_path = parse_scorecard(scorecard_path)
    if not parsed_path:
        logging.error("Parsing fehlgeschlagen. Abbruch.")
        return

    logging.info(f"Parsing erfolgreich: {parsed_path}")

    # Discord Nachricht senden
    try:
        send_discord_message(parsed_path)
    except Exception as e:
        logging.exception(f"Fehler beim Senden an Discord: {e}")
        return

    logging.info("DPWT Marcel Follow abgeschlossen.")


# --------------------------------------------------------------------
# Start
# --------------------------------------------------------------------
if __name__ == "__main__":
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logging.info(f"Bot gestartet um {start_time}")
    main()