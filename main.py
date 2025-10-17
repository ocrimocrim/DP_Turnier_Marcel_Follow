#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import logging
from urllib.parse import urlparse, urlunparse

from event_id import extract_event_id, build_leaderboard_page
from scorecard import fetch_scorecard, build_snapshot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

USAGE = """\
Verwendung:
  python main.py <Event-URL ODER Leaderboard-URL>

Beispiele:
  python main.py https://www.europeantour.com/dpworld-tour/dp-world-india-championship-2025/
  python main.py https://www.europeantour.com/dpworld-tour/dp-world-india-championship-2025/leaderboard?round=4
"""

def event_base_url_from_any(url: str) -> str:
    pu = urlparse(url)
    parts = pu.path.rstrip("/").split("/")
    if parts and parts[-1].startswith("leaderboard"):
        parts = parts[:-1]
    base_path = "/".join(parts) + "/"
    return urlunparse((pu.scheme, pu.netloc, base_path, "", "", ""))

def main():
    if len(sys.argv) != 2:
        print(USAGE)
        sys.exit(1)

    raw_url = sys.argv[1].strip()
    if not raw_url.startswith(("http://", "https://")):
        print(USAGE)
        sys.exit(1)

    # 1) Event-Basis-URL ableiten, Leaderboard-URL nur fürs Log
    event_base_url = event_base_url_from_any(raw_url)
    leaderboard_url = build_leaderboard_page(event_base_url)
    logging.info(f"Leaderboard Seite {leaderboard_url}")

    # 2) EventId ziehen (Subtask 1)
    eid = extract_event_id(event_base_url)
    if not eid:
        logging.info("EventId wurde nicht gefunden.")
        sys.exit(2)
    logging.info(f"EventId {eid}")

    # 3) Scorecard holen (Subtask 2)
    sc = fetch_scorecard(eid)
    snap = build_snapshot(sc)  # nimmt default: höchste vorhandene Runde

    # 4) Ausgabe – kompakt und maschinenlesbar
    print("--- SCORECARD SNAPSHOT ---")
    print(f"EventId:      {snap['eventId']}")
    print(f"PlayerId:     {snap['playerId']}")
    print(f"LastUpdated:  {snap['lastUpdated']}")

    r = snap["round"]
    if r:
        print(f"RoundNo:      {r['roundNo']}  (Course {r['courseNo']})")
        print(f"Strokes:      IN {r['strokesIn']}  OUT {r['strokesOut']}  TOTAL {r['strokesTotal']}  (ToPar {r['scoreToPar']})")
        print(f"HolesPlayed:
