# fetch_scorecard.py
import os
import logging
import requests

DATA_DIR = "data"
PLAYER_ID = 35703  # Marcel Schneider

def fetch_scorecard(event_id: int) -> str | None:
    """
    Holt die Scorecard von Marcel Schneider über die Sportdata-API.
    Speichert sie als JSON im data/-Ordner.
    Gibt den Pfad zur gespeicherten Datei zurück.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    url = f"https://www.europeantour.com/api/sportdata/Scorecard/Strokeplay/Event/{event_id}/Player/{PLAYER_ID}"

    logging.info(f"Abruf Scorecard: {url}")

    try:
        r = requests.get(url, timeout=20)
        if r.status_code != 200:
            logging.error(f"Fehler beim Abruf der Scorecard: HTTP {r.status_code}")
            return None
    except Exception as e:
        logging.exception(f"Fehler bei HTTP-Request: {e}")
        return None

    output_path = os.path.join(DATA_DIR, f"scorecard_{PLAYER_ID}.json")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(r.text)

    logging.info(f"Scorecard gespeichert unter {output_path}")
    return output_path