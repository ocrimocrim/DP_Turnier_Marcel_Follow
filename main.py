# main.py
import logging
import os
from datetime import datetime
from event_id import get_event_id
from parser import parse_scorecard
from discord_notifier import send_discord_update

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

def main():
    logging.info("Starte DPWT Marcel Follow Bot")

    try:
        # 1) Event-ID abrufen
        event_id = get_event_id()
        if not event_id:
            logging.error("Keine Event-ID gefunden. Abbruch.")
            return
        logging.info(f"Aktive Event-ID: {event_id}")

        # 2) Scorecard abrufen und speichern
        player_id = 35703  # Marcel Schneider
        scorecard_url = f"https://www.europeantour.com/api/sportdata/Scorecard/Strokeplay/Event/{event_id}/Player/{player_id}"

        import requests
        response = requests.get(scorecard_url, timeout=20)
        if response.status_code != 200:
            logging.error(f"Fehler beim Abruf der Scorecard: HTTP {response.status_code}")
            return

        raw_path = os.path.join(DATA_DIR, f"scorecard_{player_id}.json")
        with open(raw_path, "w", encoding="utf-8") as f:
            f.write(response.text)
        logging.info(f"Scorecard gespeichert unter {raw_path}")

        # 3) Scorecard parsen
        parsed_path = parse_scorecard(raw_path)
        if not parsed_path:
            logging.warning("Keine Scorecard-Daten geparst.")
            return

        # 4) Discord-Update senden
        send_discord_update(parsed_path)

        logging.info("Durchlauf abgeschlossen")

    except Exception as e:
        logging.exception(f"Fehler im Hauptlauf: {e}")

if __name__ == "__main__":
    logging.info(f"--- Lauf gestartet {datetime.utcnow().isoformat()} ---")
    main()
    logging.info(f"--- Lauf beendet {datetime.utcnow().isoformat()} ---")