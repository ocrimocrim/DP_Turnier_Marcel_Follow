# diff_checker.py
import json
import os
import logging
from typing import Tuple

DATA_DIR = "data"
LAST_FILE = os.path.join(DATA_DIR, "last_scorecard.json")

def load_json(path: str) -> dict:
    """Hilfsfunktion: JSON aus Datei laden."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(path: str, data: dict) -> None:
    """Hilfsfunktion: JSON speichern."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def compare_scorecards(current_path: str) -> Tuple[bool, str]:
    """
    Vergleicht die aktuelle Scorecard mit der letzten gespeicherten.
    Rückgabe: (True, Grund) wenn Unterschiede erkannt werden.
    """
    if not os.path.exists(current_path):
        logging.warning("Aktuelle Scorecard-Datei fehlt.")
        return False, "Fehler: Keine Scorecard gefunden."

    current = load_json(current_path)
    previous = load_json(LAST_FILE)

    if not previous:
        save_json(LAST_FILE, current)
        logging.info("Erster Durchlauf – keine Vergleichsdaten vorhanden.")
        return True, "Erste Speicherung"

    # Vergleiche Rundenzahl und Scores
    current_rounds = current.get("Rounds", [])
    previous_rounds = previous.get("Rounds", [])

    if len(current_rounds) != len(previous_rounds):
        save_json(LAST_FILE, current)
        return True, f"Neue Runde erkannt: {len(current_rounds)} Runden jetzt."

    # Falls gleich viele Runden: prüfen, ob Scores sich verändert haben
    for i, (curr, prev) in enumerate(zip(current_rounds, previous_rounds), start=1):
        if curr.get("Strokes") != prev.get("Strokes") or curr.get("ScoreToPar") != prev.get("ScoreToPar"):
            save_json(LAST_FILE, current)
            return True, f"Score-Änderung in Runde {i} erkannt."

        # Falls Lochdaten unterschiedlich sind
        curr_holes = curr.get("Holes", [])
        prev_holes = prev.get("Holes", [])
        if len(curr_holes) != len(prev_holes):
            save_json(LAST_FILE, current)
            return True, f"Neue Lochdaten in Runde {i} erkannt."

        for h_curr, h_prev in zip(curr_holes, prev_holes):
            if h_curr.get("Strokes") != h_prev.get("Strokes"):
                save_json(LAST_FILE, current)
                return True, f"Score-Update auf Loch {h_curr.get('HoleNo')} in Runde {i}"

    # Wenn nichts geändert
    return False, "Keine Änderung festgestellt."

if __name__ == "__main__":
    # Testlauf
    test_file = os.path.join(DATA_DIR, "scorecard_35703.json")
    changed, reason = compare_scorecards(test_file)
    print(changed, reason)