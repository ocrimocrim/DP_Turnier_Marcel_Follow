# tournament_checker.py
import requests
from bs4 import BeautifulSoup
import logging
import os
from datetime import datetime, timedelta
from discord_notify import send_discord_message

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "https://discord.com/api/webhooks/DEIN_WEBHOOK_LINK")
MARCEL_URL = "https://www.europeantour.com/players/marcel-schneider-35703/?tour=dpworld-tour"

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

def get_upcoming_tournament() -> dict | None:
    """
    Prüft die Spielerprofilseite von Marcel Schneider und gibt das nächste Turnier zurück.
    """
    try:
        response = requests.get(MARCEL_URL, timeout=20)
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Fehler beim Abrufen der Spielerprofilseite: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    playing_section = soup.find("section", {"data-testid": "playing-this-week"})

    if not playing_section:
        logging.info("Kein 'Playing this week' gefunden.")
        return None

    link_tag = playing_section.find("a", href=True)
    if not link_tag:
        logging.info("Kein Turnierlink gefunden.")
        return None

    name_tag = link_tag.find("p")
    tournament_name = name_tag.text.strip() if name_tag else "Unbekanntes Turnier"
    slug = link_tag["href"]

    return {
        "name": tournament_name,
        "slug": slug,
        "url": f"https://www.europeantour.com{slug}"
    }

def send_discord_preannouncement(tournament: dict):
    """
    Sendet eine Discord-Nachricht über ein kommendes Turnier.
    """
    message = {
        "embeds": [{
            "title": f"🏆 Neues Turnier für Marcel Schneider",
            "description": f"{tournament['name']}\n{tournament['url']}\n\nStartet morgen!",
            "color": 15844367,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=10)
        response.raise_for_status()
        logging.info(f"Discord-Vorankündigung gesendet: {tournament['name']}")
    except Exception as e:
        logging.error(f"Fehler beim Discord-Versand: {e}")

def main():
    logging.info("Prüfe, ob Marcel Schneider diese Woche spielt ...")
    tournament = get_upcoming_tournament()

    if not tournament:
        logging.info("Kein Turnier gefunden. Beende Check.")
        return

    # (Optional) Später mit API-Datum prüfen, aktuell einfach 'morgen' annehmen
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)

    # Schickt Meldung, wenn ein Turnier existiert
    send_discord_preannouncement(tournament)
    logging.info(f"Vorankündigung gesendet: {tournament['name']} ({tournament['url']})")

if __name__ == "__main__":
    main()