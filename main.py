import logging
import os
import json
import requests
from datetime import datetime
from event_id import get_event_id
from parser import parse_scorecard
from discord_notify import send_discord_message
from diff_checker import compare_scorecards

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
    Holt die Scorecard für Marcel Schneider vom aktuellen Event
    und speichert sie roh im data-Verzeichnis.
    """
    url = f"{BASE_URL}/{event_id}/Player/{player_id}"
    os.makedirs(DATA_DIR, exist_ok=True)
    output_path = os.path.join(DATA_DIR, f"scorecard_{player_id}.json")

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logging.info(f"Scorecard gespeichert unter {output_path}")
        return output_path

    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Scorecard: {e}")
        return ""

def main():
    """
    Ablauf:
    1. Aktuelles Event ermitteln
    2. Scorecard laden
    3. Änderungen prüfen
    4. Wenn neu -> parsen und an Discord senden
    """
    logging.info("Starte DP World Tour Tracker für Marcel Schneider")

    # Schritt 1 – Event-ID ermitteln
    try:
        event_id = get_event_id()
        logging.info(f"Aktuelles Event erkannt (Event-ID: {event_id})")
    except Exception as e:
        logging.error(f"Event-ID konnte nicht ermittelt werden: {e}")
        return

    # Schritt 2 – Scorecard abrufen
    scorecard_path = fetch_scorecard(event_id, PLAYER_ID)
    if not scorecard_path:
        logging.error("Scorecard konnte nicht geladen werden.")
        return

    # Schritt 3 – Änderungen erkennen
    changed, reason = compare_scorecards(scorecard_path)
    if not changed:
        logging.info("Keine Änderungen seit letztem Lauf. Stoppe.")
        return
    logging.info(f"Änderung erkannt: {reason}")

    # Schritt 4 – Scorecard parsen
    try:
        parsed_path = parse_scorecard(scorecard_path)
        logging.info(f"Scorecard geparst: {parsed_path}")
    except Exception as e:
        logging.error(f"Fehler beim Parsen: {e}")
        return

    # Schritt 5 – Discord-Benachrichtigung senden
    try:
        send_discord_message(parsed_path)
        logging.info("Discord-Update erfolgreich gesendet.")
    except Exception as e:
        logging.error(f"Discord-Senden fehlgeschlagen: {e}")

    logging.info("Workflow abgeschlossen.")

if __name__ == "__main__":
    main()