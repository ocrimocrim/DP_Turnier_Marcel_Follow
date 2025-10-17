# parser.py
import json
import os
import logging
from datetime import datetime

DATA_DIR = "data"
INPUT_FILE = os.path.join(DATA_DIR, "scorecard_35703.json")

def parse_scorecard(input_path: str = INPUT_FILE) -> str:
    """
    Liest die gespeicherte Scorecard (roh) von Marcel Schneider
    und speichert pro Runde ein aufbereitetes JSON mit allen Lochdaten.
    Rückgabe: Pfad zur neuen Datei.
    """
    if not os.path.exists(input_path):
        logging.error(f"Eingabedatei fehlt: {input_path}")
        raise FileNotFoundError(input_path)

    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    event_id = raw_data.get("EventId")
    player_id = raw_data.get("PlayerId")
    rounds = raw_data.get("Rounds", [])

    if not rounds:
        logging.warning(f"Keine Runden in Scorecard gefunden ({input_path})")
        return ""

    parsed = {
        "event_id": event_id,
        "player_id": player_id,
        "timestamp": datetime.utcnow().isoformat(),
        "rounds": []
    }

    for rnd in rounds:
        round_no = rnd.get("RoundNo")
        course_no = rnd.get("CourseNo")
        strokes = rnd.get("Strokes")
        score_to_par = rnd.get("ScoreToPar")
        holes = rnd.get("Holes", [])

        parsed_round = {
            "round_no": round_no,
            "course_no": course_no,
            "strokes": strokes,
            "score_to_par": score_to_par,
            "holes_played": len(holes),
            "holes": []
        }

        for hole in holes:
            parsed_round["holes"].append({
                "hole_no": hole.get("HoleNo"),
                "strokes": hole.get("Strokes"),
                "score_class": hole.get("ScoreClass"),
                "is_am_score": hole.get("IsAmScore"),
                "penalty": hole.get("Penalty")
            })

        parsed["rounds"].append(parsed_round)

    # Speicherpfad mit Zeitstempel
    timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
    output_path = os.path.join(DATA_DIR, f"parsed_scorecard_35703_{timestamp}.json")

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as out:
        json.dump(parsed, out, indent=2, ensure_ascii=False)

    logging.info(f"Parsed Scorecard gespeichert unter {output_path}")
    return output_path