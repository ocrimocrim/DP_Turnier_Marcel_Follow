# scorecard.py
import logging
import os
import json
import requests

API_BASE = "https://www.europeantour.com/api/sportdata/Scorecard/Strokeplay/Event"
MARCEL_ID = 35703
DATA_DIR = "data"
FILENAME = f"scorecard_{MARCEL_ID}.json"

def fetch_scorecard(event_id: int) -> str:
    """
    Holt die Scorecard von Marcel Schneider für das angegebene Event
    und speichert sie roh als JSON-Datei unter data/scorecard_35703.json.
    Gibt den Pfad zur Datei zurück.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    url = f"{API_BASE}/{event_id}/Player/{MARCEL_ID}"
    logging.info(f"Rufe Scorecard ab: {url}")

    try:
        response = requests.get(url, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Fehler beim Abrufen der Scorecard: {e}")
        raise

    try:
        data = response.json()
    except ValueError as e:
        logging.error(f"Ungültige JSON-Antwort: {e}")
        raise

    file_path = os.path.join(DATA_DIR, FILENAME)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Scorecard gespeichert unter {file_path}")
    except OSError as e:
        logging.error(f"Fehler beim Schreiben der Datei: {e}")
        raise

    return file_path