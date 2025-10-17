import json
import requests
import logging
from datetime import datetime
import os

# Discord Webhook URL – hier deine eigene einsetzen
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/DEIN_WEBHOOK_LINK")

def send_discord_message(parsed_json_path: str) -> None:
    """
    Sendet eine Discord-Nachricht mit Scorecard-Daten (Marcel Schneider)
    an den definierten Webhook. Nimmt den Pfad zur JSON-Datei aus parser.py.
    """

    if not os.path.exists(parsed_json_path):
        logging.error(f"Datei für Discord-Post nicht gefunden: {parsed_json_path}")
        return

    with open(parsed_json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    event_id = data.get("event_id")
    player_id = data.get("player_id")
    timestamp = data.get("timestamp")
    rounds = data.get("rounds", [])

    if not rounds:
        logging.warning("Keine Runden gefunden – nichts zu posten.")
        return

    latest_round = rounds[-1]
    round_no = latest_round.get("round_no")
    strokes = latest_round.get("strokes")
    score_to_par = latest_round.get("score_to_par")
    holes = latest_round.get("holes", [])

    # Nachrichtentitel
    title = f"🏌️ Marcel Schneider – Runde {round_no}"

    # Score-Header
    header = f"Schläge: **{strokes}**, Par: **{score_to_par:+}**"

    # Hole-by-Hole-Details als String
    holes_text = ""
    for hole in holes:
        holes_text += f"Hole {hole.get('hole_no')}: {hole.get('strokes')} ({hole.get('score_class')})\n"

    # Discord Payload
    embed = {
        "title": title,
        "description": f"{header}\n\n{holes_text}",
        "color": 3447003,
        "footer": {
            "text": f"Event-ID {event_id} | Player-ID {player_id} | {timestamp}"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

    payload = {"embeds": [embed]}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        response.raise_for_status()
        logging.info(f"Discord-Post erfolgreich: Runde {round_no}")
    except Exception as e:
        logging.error(f"Fehler beim Senden an Discord: {e}")