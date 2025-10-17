import logging
import os
from event_id import get_event_id
from parser import parse_scorecard
from discord_notify import send_discord_message
import requests
import json
from datetime import datetime

DATA_DIR = "data"
PLAYER_ID = 35703  # Marcel Schneider
BASE_URL = "https://www.europeantour.com/api/sportdata/Scorecard/Strokeplay/Event"

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

def fetch_scorecard(event_id: int, player_id: int = PLAYER_ID) -> str:
    """
    Lädt die Scorecard von Marcel Schneider für das aktuelle Event.
    Speichert sie als JSON im data-Verzeichnis und gibt den Pfad zurück.
    """
    url = f"{BASE_URL}/{event_id}/Player/{player_id}"
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, f"scorecard_{player_id}.json")

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logging.info(f"Scorecard gespeichert unter {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Fehler beim Laden der Scorecard: {e}")
        return ""

def main():
    """
    Hauptablauf:
    1. Event-ID ermitteln
    2. Scorecard von Marcel abrufen
    3. Scorecard parsen
    4. Discord-Benachrichtigung senden
    """
    logging.info("Starte DP World Tour – Marcel Schneider Follow")

    # Schritt 1: Event-ID holen
    try:
        event_id = get_event_id()
        logging.info(f"Aktuelles Event gefunden (Event-ID: {event_id})")
    except Exception as e:
        logging.error(f"Event-ID konnte nicht ermittelt werden: {e}")
        return

    # Schritt 2: Scorecard holen
    scorecard_path = fetch_scorecard(event_id, PLAYER_ID)
    if not scorecard_path:
        logging.error("Scorecard konnte nicht geladen werden.")
        return

    # Schritt 3: Scorecard parsen
    parsed_path = parse_scorecard(scorecard_path)
    if not parsed_path:
        logging.error("Scorecard konnte nicht verarbeitet werden.")
        return

    # Schritt 4: An Discord senden
    try:
        send_discord_message(parsed_path)
    except Exception as e:
        logging.error(f"Fehler beim Senden an Discord: {e}")

    logging.info("Prozess abgeschlossen.")

if __name__ == "__main__":
    main()