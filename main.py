# main.py
import logging
from event_id import extract_event_id
from scorecard import fetch_scorecard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def main():
    logging.info("Starte DPWT Marcel Bot")

    # Event ermitteln
    leaderboard_url = "https://www.europeantour.com/dpworld-tour/dp-world-india-championship-2025/leaderboard?round=4"
    event_id = extract_event_id(leaderboard_url)

    if not event_id:
        logging.error("EventId wurde nicht gefunden. Abbruch.")
        return

    logging.info(f"EventId gefunden: {event_id}")

    # Scorecard abrufen und speichern
    file_path = fetch_scorecard(event_id)
    logging.info(f"Scorecard erfolgreich gespeichert: {file_path}")

if __name__ == "__main__":
    main()