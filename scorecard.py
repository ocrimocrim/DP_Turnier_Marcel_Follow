#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Any, Dict, List, Optional, Tuple
import requests

API_SCORECARD_FMT = "https://www.europeantour.com/api/sportdata/Scorecard/Strokeplay/Event/{event_id}/Player/{player_id}"
MARCEL_ID = 35703

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "dpwt-marcel-bot/scorecard/1.0 (+github-actions)",
    "Accept": "application/json",
})

def fetch_scorecard(event_id: int, player_id: int = MARCEL_ID) -> Dict[str, Any]:
    """
    Holt die Scorecard eines Spielers (alle Runden mit Löchern).
    Erwartete Felder (aus deinem Screenshot):
      - EventId, PlayerId, LastUpdated
      - Rounds: [{ RoundNo, CourseNo, StrokesIn, StrokesOut, Strokes, ScoreToPar, Holes: [{ HoleNo, Strokes, ScoreClass, IsAmScore, Penalty }] }]
    """
    url = API_SCORECARD_FMT.format(event_id=event_id, player_id=player_id)
    logging.info(f"Scorecard API {url}")
    r = SESSION.get(url, timeout=25)
    r.raise_for_status()
    return r.json()

def _rounds(scorecard: Dict[str, Any]) -> List[Dict[str, Any]]:
    return scorecard.get("Rounds") or []

def pick_round(scorecard: Dict[str, Any], round_no: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Gibt die gewünschte Runde zurück; sonst die höchste vorhandene RoundNo."""
    rounds = _rounds(scorecard)
    if not rounds:
        return None
    if round_no is not None:
        for r in rounds:
            if r.get("RoundNo") == round_no:
                return r
        return None
    # höchste RoundNo
    return sorted(rounds, key=lambda x: x.get("RoundNo") or 0, reverse=True)[0]

def flatten_holes(round_obj: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Gibt Löcher als Liste mit robusten Keys zurück:
      [{hole: 1, strokes: 5, scoreClass: "pa", penalty: 0}, ...]
    """
    res: List[Dict[str, Any]] = []
    holes = (round_obj or {}).get("Holes") or []
    for h in holes:
        res.append({
            "hole": h.get("HoleNo"),
            "strokes": h.get("Strokes"),
            "scoreClass": h.get("ScoreClass"),  # "pa", "bi", "bo", "db", ...
            "penalty": h.get("Penalty"),
            "isAmScore": h.get("IsAmScore"),
        })
    # sortieren nach Lochnummer
    res.sort(key=lambda x: (x.get("hole") is None, x.get("hole")))
    return res

def summarize_round(round_obj: Dict[str, Any]) -> Dict[str, Any]:
    """Baut eine saubere Zusammenfassung der Runde."""
    if not round_obj:
        return {}
    return {
        "roundNo": round_obj.get("RoundNo"),
        "courseNo": round_obj.get("CourseNo"),
        "strokesIn": round_obj.get("StrokesIn"),
        "strokesOut": round_obj.get("StrokesOut"),
        "strokesTotal": round_obj.get("Strokes"),
        "scoreToPar": round_obj.get("ScoreToPar"),
        "holes": flatten_holes(round_obj),
    }

def progress(round_obj: Dict[str, Any]) -> Tuple[int, int]:
    """
    Liefert (gespielte_Löcher, verbleibende_Löcher) für die Runde.
    Annahme: 'Strokes' ist gesetzt, wenn ein Loch gespielt wurde;
             nicht gesetzte/None sind noch offen.
    """
    holes = (round_obj or {}).get("Holes") or []
    played = sum(1 for h in holes if h.get("Strokes") is not None)
    total = len(holes) if holes else 18  # Fallback 18
    return played, max(0, total - played)

def build_snapshot(scorecard: Dict[str, Any], round_no: Optional[int] = None) -> Dict[str, Any]:
    """
    Liefert ein schlankes Objekt für Ausgabe/Weiterverarbeitung.
    """
    r = pick_round(scorecard, round_no=round_no)
    played, remaining = progress(r) if r else (0, 0)
    return {
        "eventId": scorecard.get("EventId"),
        "playerId": scorecard.get("PlayerId"),
        "lastUpdated": scorecard.get("LastUpdated"),
        "round": summarize_round(r) if r else None,
        "holesPlayed": played,
        "holesRemaining": remaining,
    }
