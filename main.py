# main.py
import os
import json
import logging
from datetime import datetime
import requests

from event_id import get_event_id
from parser import parse_scorecard

# Logging vorbereiten
LOG_DIR = "logs"
DATA_DIR = "data"
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

log_file = os.path.join(LOG_DIR, f"run_{datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%S')}.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

PLAYER_ID = 35703  # Marcel Schneider
BASE_URL = "https://www.europeantour.com/api/sportdata/Scorecard/Strokeplay/Event"

def download_scorecard(event_id: int, player_id: int = PLAYER_ID) -> str:
    """
    Holt Scorecard von der DP World Tour API für einen Spieler und speichert sie roh.
    Rückgabe: Pfad zur gespeicherten Datei.
    """
    url = f"{BASE_URL}/{event_id}/Player/{player_id}"
    logging.info(f"Scorecard-Request: {url}")

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Fehler beim Laden der Scorecard: {e}")
        raise

    data = response.json()

    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    output_path = os.path.join(DATA_DIR, f"scorecard_{player_id}_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logging.info(f"Scorecard gespeichert unter {output_path}")
    return output_path


def main():
    logging.info("Starte DP World Tour Scorecard-Workflow für Marcel Schneider")

    try:
        event_id = get_event_id()
        logging.info(f"Aktuelle Event-ID: {event_id}")
    except Exception as e:
        logging.error(f"Event-ID konnte nicht ermittelt werden: {e}")
        return

    try:
        raw_path = download_scorecard(event_id, PLAYER_ID)
        logging.info("Scorecard erfolgreich geladen")
    except Exception as e:
        logging.error(f"Scorecard-Download fehlgeschlagen: {e}")
        return

    try:
        parsed_path = parse_scorecard(raw_path)
        logging.info(f"Scorecard erfolgreich geparst: {parsed_path}")
    except Exception as e:
        logging.error(f"Parsing fehlgeschlagen: {e}")

    logging.info("Workflow abgeschlossen")


if __name__ == "__main__":
    main()