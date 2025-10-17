# event_id.py
import re, json, logging
from urllib.parse import urlparse, urljoin, urlencode
import requests

BASE = "https://www.europeantour.com"
JINA = "https://r.jina.ai/http://"

# ---------------- HTTP ----------------
SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "dpwt-marcel-bot/eventid/3.0 (+github-actions)",
    "Accept": "text/html,application/json"
})

def _get(url: str, allow_jina: bool = False) -> str:
    tries = []
    if allow_jina:
        # Jina voranstellen, damit statische Inhalte auch ohne JS erreichbar sind
        if url.startswith("https://"):
            tries.append(JINA + url[len("https://"):])
        elif url.startswith("http://"):
            tries.append(JINA + url[len("http://"):])
        else:
            tries.append(JINA + url)
    tries.append(url)

    last_err = None
    for u in tries:
        logging.debug(f"GET {u}")
        try:
            r = SESSION.get(u, timeout=25)
            if r.status_code == 200:
                return r.text
            last_err = f"http {r.status_code}"
        except Exception as e:
            last_err = str(e)
    raise RuntimeError(f"fetch failed for {url} because {last_err}")

# ------------- Patterns ---------------
RX_EVENT_LOAD_URL     = re.compile(r'/api/sportdata/Leaderboard/Strokeplay/(\d+)/type/load', re.I)
RX_EVENT_ID_KEY       = re.compile(r'"(?:EventId|eventId)"\s*:\s*(\d+)', re.I)
RX_LEADERBOARD_DOC_ID = re.compile(r'"id"\s*:\s*"leaderboard-strokeplay-(\d+)"', re.I)
RX_SCRIPT_SRC         = re.compile(r'<script[^>]+src="([^"]+?/dist/js/[^"]+?\.js)"', re.I)

RESOLVER_PATHS = [
    "/api/cms/page-resolver",
    "/api/cms/resolve",
    "/api/seo/resolve",
]

# ------------- Helpers ----------------
def build_leaderboard_page(event_page_url: str) -> str:
    return urljoin(event_page_url.rstrip("/") + "/", "leaderboard?round=4")

def _deep_find_event_id(x) -> int | None:
    if isinstance(x, dict):
        for k, v in x.items():
            if k in ("EventId", "eventId") and isinstance(v, int):
                return int(v)
            got = _deep_find_event_id(v)
            if got:
                return got
    elif isinstance(x, list):
        for v in x:
            got = _deep_find_event_id(v)
            if got:
                return got
    elif isinstance(x, str):
        m = RX_EVENT_LOAD_URL.search(x) or RX_LEADERBOARD_DOC_ID.search(x)
        if m:
            return int(m.group(1))
    return None

def _event_id_from_text(blob: str) -> int | None:
    # 1) direkte Sportdata-URL im Text
    m = RX_EVENT_LOAD_URL.search(blob)
    if m:
        try: return int(m.group(1))
        except: pass
    # 2) "leaderboard-strokeplay-<id>"
    m = RX_LEADERBOARD_DOC_ID.search(blob)
    if m:
        try: return int(m.group(1))
        except: pass
    # 3) "EventId": <id>
    m = RX_EVENT_ID_KEY.search(blob)
    if m:
        try: return int(m.group(1))
        except: pass
    # 4) eingebettete JSON-Blöcke durchsuchen
    for m in re.finditer(r'<script[^>]*>\s*({.*?})\s*</script>', blob, re.S | re.I):
        raw = m.group(1)
        for candidate in (raw, re.sub(r'(?://.*?$)|/\*.*?\*/', '', raw, flags=re.M | re.S)):
            try:
                j = json.loads(candidate)
            except Exception:
                continue
            got = _deep_find_event_id(j)
            if got:
                return got
    return None

def _call_resolvers_for_path(path: str) -> int | None:
    """Ruft die internen Resolver mit dem Seitenpfad auf und versucht, die ID aus deren JSON zu ziehen."""
    for base_path in RESOLVER_PATHS:
        url = f"{BASE}{base_path}?{urlencode({'path': path})}"
        try:
            txt = _get(url, allow_jina=False)  # Resolver direkt
        except Exception as e:
            logging.debug(f"resolver miss {url} because {e}")
            continue

        # schnelle Treffer
        for rx in (RX_EVENT_LOAD_URL, RX_LEADERBOARD_DOC_ID, RX_EVENT_ID_KEY):
            m = rx.search(txt)
            if m:
                try: return int(m.group(1))
                except: continue

        # strukturiert parsen
        try:
            data = json.loads(txt)
        except Exception:
            data = None
        if data is not None:
            got = _deep_find_event_id(data)
            if got:
                return got
    return None

# ------------- PUBLIC API -------------
def extract_event_id(event_page_url: str) -> int | None:
    """
    Holt die EventId ausschließlich *von der Leaderboard-Seite mit round=4*.
    Reihenfolge:
      1) Leaderboard HTML via Jina → direkte Muster / JSON
      2) Leaderboard HTML direkt (ohne Proxy) → direkte Muster / JSON
      3) Resolver-APIs für denselben Pfad (mit und ohne ?round=4)
      4) Als Zusatz: geladene JS-Bundles (/dist/js/*.js) abklappern und dort nach Mustern suchen
    """
    lb_url = build_leaderboard_page(event_page_url)
    # 1) via Jina
    try:
        html_jina = _get(lb_url, allow_jina=True)
        eid = _event_id_from_text(html_jina)
        if eid:
            logging.info(f"EventId Quelle Leaderboard (Jina) {eid}")
            return eid
    except Exception as e:
        logging.debug(f"leaderboard via Jina miss: {e}")

    # 2) direkt
    try:
        html_direct = _get(lb_url, allow_jina=False)
        eid = _event_id_from_text(html_direct)
        if eid:
            logging.info(f"EventId Quelle Leaderboard (direct) {eid}")
            return eid
    except Exception as e:
        logging.debug(f"leaderboard direct miss: {e}")

    # 3) Resolver-APIs für denselben Pfad
    path_with_round = urlparse(lb_url).path  # nur der Pfad, Query wird von Resolver ohnehin ignoriert
    eid = _call_resolvers_for_path(path_with_round)
    if eid:
        logging.info(f"EventId Quelle Resolver (with path) {eid}")
        return eid
    path_root = urlparse(event_page_url).path.rstrip("/")
    eid = _call_resolvers_for_path(path_root)
    if eid:
        logging.info(f"EventId Quelle Resolver (root) {eid}")
        return eid

    # 4) geladene JS-Bundles der Seite durchsuchen
    try:
        base_html = html_direct if 'html_direct' in locals() else _get(lb_url, allow_jina=False)
        script_srcs = RX_SCRIPT_SRC.findall(base_html)
        seen = set()
        for src in script_srcs:
            # absolute URL bauen
            src_abs = src if src.startswith("http") else urljoin(BASE, src)
            if src_abs in seen:
                continue
            seen.add(src_abs)
            try:
                js = _get(src_abs, allow_jina=False)
            except Exception as e:
                logging.debug(f"bundle miss {src_abs}: {e}")
                continue
            eid = _event_id_from_text(js)
            if eid:
                logging.info(f"EventId Quelle JS-Bundle {eid} ({src_abs.split('/')[-1]})")
                return eid
    except Exception as e:
        logging.debug(f"bundle sweep miss: {e}")

    logging.info("EventId wurde nicht gefunden")
    return None
