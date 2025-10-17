#!/usr/bin/env python3
import sys
import logging
from urllib.parse import urlparse
from event_id import extract_event_id, build_leaderboard_page

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

USAGE = """\
Verwendung:
  python main.py <event-seiten-url-oder-leaderboard-url>

Beispiel (Eventseite):
  python main.py https://www.europeantour.com/dpworld-tour/dp-world-india-championship-2025/

Beispiel (Leaderboard direkt):
  python main.py https://www.europeantour.com/dpworld-tour/dp-world-india-championship-2025/leaderboard?round=4
"""

def main():
    if len(sys.argv) != 2:
        print(USAGE)
        sys.exit(1)

    raw_url = sys.argv[1].strip()
    if not raw_url.startswith("http"):
        print(USAGE)
        sys.exit(1)

    # Falls keine round=4-URL übergeben wurde, baue sie aus der Eventseite
    path = urlparse(raw_url).path
    if not path.endswith("/leaderboard"):
        leaderboard_url = build_leaderboard_page(raw_url)
    else:
        leaderboard_url = raw_url

    logging.info(f"Leaderboard Seite {leaderboard_url}")

    # Nur Subtask 1: EventId extrahieren
    eid = extract_event_id(raw_url)  # Funktion erwartet Event-**Seiten**-URL
    if not eid:
        logging.info("EventId wurde nicht gefunden.")
        sys.exit(2)

    logging.info(f"EventId {eid}")
    print(eid)

if __name__ == "__main__":
    main()
