"""OutToday events bot (wersja 1).

Co robi, krok po kroku:
1. Bierze listę oficjalnych stron z sources/*.json.
2. Sprawdza robots.txt. Jeśli strona zabrania botom wejścia, pomija ją.
3. Otwiera stronę w prawdziwej przeglądarce (Playwright), bo wiele stron ładuje eventy JavaScriptem.
4. Porównuje tekst strony z poprzednim razem. Bez zmian = bez wywołania AI (oszczędność).
5. AI (Claude Haiku) wypisuje eventy WYŁĄCZNIE z tego, co jest na stronie, z dosłownymi cytatami.
6. Program sam sprawdza każdy cytat: jeśli cytatu nie ma na stronie, pole jest kasowane i trafia do braków.
7. Gdy czegoś brakuje, bot wchodzi na podstronę eventu (jeśli jest link) i uzupełnia.
8. Zasada wejścia: tylko konkretne wyjścia z datą. Reszta trafia do raportu jako odrzucona.
9. Zapis: nowe wpisy jako 'pending' (apka ich nie pokazuje, dopóki nie zatwierdzicie).
   Zmiany w zatwierdzonych wpisach (np. cena) idą do tabeli bot_changes, nie nadpisują niczego.
10. Raport: report.csv i podsumowanie w GitHub Actions.

Uruchomienie lokalne: python bot/run.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import glob
import hashlib
import json
import os
import re
import sys
import time
import unicodedata
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cachefix  # noqa: E402  (prompt caching + miesięczny limit AI + blokada wyszukiwania)

MODEL = os.environ.get("BOT_MODEL", "claude-haiku-5-5")
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0 Safari/537.36 OutTodayBot/0.1 (+https://outtoday.ae)"
)
ROBOTS_AGENT = "OutTodayBot"
MAX_TEXT = 80_000
MAX_LINKS = 400
PAUSE_SECONDS = 2.0
UAE_TZ = dt.timezone(dt.timedelta(hours=4))

EVENT_CATEGORIES = [
    "music", "culture", "sport", "food", "festivals",
    "nightlife", "classes", "nature", "community", "family", "market",
]
CITIES = [
    "Abu Dhabi", "Al Ain", "Dubai", "Sharjah", "Ajman",
    "Umm Al Quwain", "Ras Al Khaimah", "Fujairah",
]
MONTHS = [
    ("january", "jan"), ("february", "feb"), ("march", "mar"), ("april", "apr"),
    ("may", "may"), ("june", "jun"), ("july", "jul"), ("august", "aug"),
    ("september", "sep"), ("october", "oct"), ("november", "nov"), ("december", "dec"),
]

# ---------------------------------------------------------------- tekst


def norm(s: str | None) -> str:
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    s = s.replace("–", "-").replace("—", "-").replace(" ", " ")
    s = re.sub(r"\s+", " ", s).strip().lower()
    return s


def quote_on_page(quote: str | None, page_norm: str) -> bool:
    q = norm(quote)
    return len(q) >= 3 and q in page_norm


def today_uae() -> dt.date:
    return dt.datetime.now(UAE_TZ).date()


def parse_date(s) -> dt.date | None:
    if not s:
        return None
    try:
        return dt.date.fromisoformat(str(s)[:10])
    except ValueError:
        return None


def parse_time(s) -> str | None:
    if not s:
        return None
    m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::\d{2})?", str(s).strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if h > 23 or mi > 59:
        return None
    return f"{h:02d}:{mi:02d}"


# ---------------------------------------------------------------- pobieranie


_ROBOTS_CACHE: dict[str, tuple[int, str]] = {}
_DB = None  # ustawiane w main(); pamięć wyszukiwań (tabela bot_pages, klucz "search:...")
MAX_SEARCH_CALLS = int(os.environ.get("MAX_SEARCH_CALLS", "0"))  # strategia 20.11: domyślnie bez wyszukiwania  # limit płatnych wyszukiwań na jedno uruchomienie
_search_calls = 0


def search_budget() -> bool:
    """True = wolno jeszcze szukać w tym uruchomieniu (każde zapytanie to do 2–3 wyszukań po ~0,01 USD)."""
    global _search_calls
    if _search_calls >= MAX_SEARCH_CALLS:
        return False
    _search_calls += 1
    return True


def search_cache_get(key: str, days: int = 30):
    """Wynik wcześniejszego wyszukania: url, "" (nic nie znaleziono) albo None (brak w pamięci / przeterminowane)."""
    if not _DB:
        return None
    try:
        rows = _DB.get("bot_pages", {"select": "content_hash,last_fetched_at", "url": f"eq.search:{key}"})
    except Exception:
        return None
    if not rows:
        return None
    cutoff = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
    if (rows[0].get("last_fetched_at") or "") < cutoff:
        return None
    v = rows[0].get("content_hash") or "-"
    return "" if v == "-" else v


def search_cache_put(key: str, value: str | None) -> None:
    if not _DB:
        return
    try:
        _DB.upsert("bot_pages", {"url": f"search:{key}", "content_hash": value or "-",
                                 "last_fetched_at": dt.datetime.now(dt.timezone.utc).isoformat(), "last_status": "search"}, "url")
    except Exception as e:
        print(f"   [pamięć wyszukiwań] {e}")


_BROWSER = None  # ustawiane w main(); robots.txt czytamy przez przeglądarkę, gdy zwykłe pobieranie ma problem z certyfikatem


def _get_robots(robots_url: str) -> tuple[int, str]:
    if robots_url in _ROBOTS_CACHE:
        return _ROBOTS_CACHE[robots_url]
    try:
        r = requests.get(robots_url, headers={"User-Agent": USER_AGENT}, timeout=20)
        res = (r.status_code, r.text)
    except requests.exceptions.SSLError:
        res = _BROWSER.fetch_raw(robots_url) if _BROWSER else (-1, "")
    except requests.RequestException:
        res = (-1, "")
    _ROBOTS_CACHE[robots_url] = res
    return res


def robots_allows(url: str) -> tuple[bool, str]:
    """Zasady RFC 9309: brak pliku (4xx) = wolno; błąd serwera lub brak odpowiedzi = dziś nie wchodzimy."""
    p = urlparse(url)
    status, body = _get_robots(f"{p.scheme}://{p.netloc}/robots.txt")
    if status == -1:
        return False, "robots.txt nie odpowiada, dziś pomijam"
    if status >= 500 or status == 429:
        return False, f"robots.txt błąd serwera ({status}), dziś pomijam"
    if status >= 400:
        return True, f"brak robots.txt ({status})"
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(body.splitlines())
    ok = rp.can_fetch(ROBOTS_AGENT, url)
    return ok, "robots.txt pozwala" if ok else "robots.txt ZABRANIA"


class Browser:
    """Prawdziwa przeglądarka (Chromium), żeby widzieć eventy ładowane JavaScriptem."""

    def __init__(self):
        self._pw = None
        self._browser = None

    def __enter__(self):
        try:
            from playwright.sync_api import sync_playwright
            self._pw = sync_playwright().start()
            self._browser = self._pw.chromium.launch()
        except Exception as e:  # brak przeglądarki: zwykłe pobieranie
            print(f"[uwaga] Playwright niedostępny ({e}); używam zwykłego pobierania")
            self._browser = None
        return self

    def __exit__(self, *a):
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def fetch_raw(self, url: str) -> tuple[int, str]:
        """Surowy tekst pliku (np. robots.txt) przez przeglądarkę."""
        if not self._browser:
            return (-1, "")
        ctx = self._browser.new_context(user_agent=USER_AGENT)
        try:
            page = ctx.new_page()
            resp = page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            if not resp:
                return (-1, "")
            try:
                body = resp.text()
            except Exception:
                body = page.inner_text("body")
            return (resp.status, body)
        except Exception:
            return (-1, "")
        finally:
            ctx.close()

    def fetch(self, url: str) -> dict:
        """Jak _fetch, ale w trybie paczki drugie przejście bierze stronę z pamięci (bez ponownego pobierania)."""
        memo = self.__dict__.setdefault("_memo", {})
        if BATCH["mode"] == "use" and url in memo:
            return memo[url]
        page = self._fetch(url)
        if BATCH["mode"] == "collect":
            memo[url] = page
        return page

    def _fetch(self, url: str) -> dict:
        if self._browser:
            ctx = self._browser.new_context(user_agent=USER_AGENT, locale="en-US")
            page = ctx.new_page()
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=45_000)
                try:
                    page.wait_for_load_state("networkidle", timeout=15_000)
                except Exception:
                    pass
                # przewiń, żeby doładowały się listy z "lazy loading"
                for _ in range(4):
                    page.mouse.wheel(0, 4000)
                    page.wait_for_timeout(700)
                full = page.inner_text("body")
                # Bez menu, stopki i banerów cookies: mniej tokenów do AI (oszczędność), treść eventów zostaje.
                try:
                    lean = page.evaluate("""() => {
                        const b = document.body.cloneNode(true);
                        b.querySelectorAll('nav, footer, [role=navigation], [role=contentinfo], script, style, noscript, svg, '
                          + '[id*=cookie i], [class*=cookie i], [id*=consent i], [class*=consent i], [class*=newsletter i]')
                          .forEach(e => e.remove());
                        document.documentElement.appendChild(b); b.style.display = 'block';
                        const t = b.innerText; b.remove(); return t;
                    }""")
                except Exception:
                    lean = ""
                text = slim_text(lean if lean and len(lean) > max(500, 0.3 * len(full)) else full)
                links = page.eval_on_selector_all(
                    "a[href]",
                    "els => els.map(a => [(a.innerText || a.getAttribute('aria-label') || '').trim().slice(0,150), a.href])",
                )
                status = resp.status if resp else 0
                final_url = page.url
            finally:
                ctx.close()
            return {"status": status, "text": text, "full_text": full, "links": links, "final_url": final_url}

        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=45)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(r.text, "html.parser")
        for t in soup(["script", "style", "noscript"]):
            t.decompose()
        links = [[a.get_text(" ", strip=True)[:150], urljoin(r.url, a["href"])] for a in soup.find_all("a", href=True)]
        full = soup.get_text("\n", strip=True)
        for t in soup(["nav", "footer"]):
            t.decompose()
        lean = soup.get_text("\n", strip=True)
        text = slim_text(lean if len(lean) > max(500, 0.3 * len(full)) else full)
        return {"status": r.status_code, "text": text, "full_text": full, "links": links, "final_url": r.url}


def slim_text(t: str) -> str:
    """Usuwa puste i powtarzające się linie (menu, przyciski "Book now" itp.) – mniej tokenów, ta sama treść."""
    seen: dict[str, int] = {}
    out = []
    for line in (t or "").splitlines():
        x = line.strip()
        if not x:
            continue
        k = x.lower()
        seen[k] = seen.get(k, 0) + 1
        if len(x) < 40 and seen[k] > 2:  # krótkie powtórki ("Book now", "Read more") – zostawiamy dwie
            continue
        if out and out[-1] == x:
            continue
        out.append(x)
    return "\n".join(out)


TICKET_SELLERS = ("district.ae", "platinumlist.net", "ticketmaster", "livenation.me", "ticketsmarche", "800tickets", "q-tickets",
                  "tixbox", "eventbrite", "virginmegastore", "etix.com", "ticketingbox", "dubaiopera.com")


def ticket_links(links: list) -> list[str]:
    out = []
    for _, href in links:
        u = urlparse(href or "")
        if href and href.startswith("http") and len(u.path.strip("/")) > 3 and any(t in u.netloc.lower() for t in TICKET_SELLERS):
            h = href.split("#")[0]
            if h not in out:
                out.append(h)
    return out[:3]


AGGREGATORS = ("platinumlist", "feverup", "yallaabudhabi", "whatson.ae", "timeoutdubai", "wow-rak", "koobit",
               "facebook.com", "instagram.com", "twitter.com", "x.com", "youtube.com", "tiktok.com", "linkedin.com",
               "google.", "apple.com", "wa.me", "whatsapp")


def external_links(links: list, base: str) -> list[tuple[str, str]]:
    """Linki do stron organizatorów (inne domeny), bez portali i mediów społecznościowych."""
    seen, out = set(), []
    for label, href in links:
        if not href or not href.startswith("http") or same_site(href, base):
            continue
        host = urlparse(href).netloc.lower()
        if any(a in host for a in AGGREGATORS) or href in seen:
            continue
        seen.add(href)
        out.append((re.sub(r"\s+", " ", label or "").strip(), href.split("#")[0]))
    return out[:150]


def same_site(a: str, b: str) -> bool:
    ha, hb = urlparse(a).netloc.lower(), urlparse(b).netloc.lower()
    strip = lambda h: h[4:] if h.startswith("www.") else h
    return strip(ha) == strip(hb)


def clean_links(links: list, base: str) -> list[tuple[str, str]]:
    seen, out = set(), []
    for label, href in links:
        if not href or not href.startswith("http") or not same_site(href, base):
            continue
        href = href.split("#")[0]
        if href in seen:
            continue
        seen.add(href)
        out.append((re.sub(r"\s+", " ", label or "").strip(), href))
    return out[:MAX_LINKS]


# ---------------------------------------------------------------- AI

ITEM_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string", "description": "Event name as written on the page. If it is not in English (e.g. Arabic or Russian), give an English translation, keeping proper names, and add ' (in Arabic)' / ' (in Russian)' when the event itself is held in that language. The original wording goes in evidence.title. Write titles in normal capitalisation, not ALL CAPS (e.g. 'CHICAGO THE MUSICAL' -> 'Chicago the Musical'), keeping acronyms like IIFA or UAE."},
        "category": {"type": "string", "enum": EVENT_CATEGORIES, "description": (
            "music = concerts, DJ sets, opera, musicals, stand-up comedy shows (always music, never nightlife) and stage shows; "
            "culture = exhibitions, talks, film screenings, theatre plays, heritage; "
            "family = activities aimed at children or families (kids' shows, family days, games, storytelling, kids' workshops); "
            "classes = workshops and courses for adults; sport = matches, races, runs, fitness; "
            "food = food festivals, tastings, dining events; festivals = multi-day festivals and seasonal villages; "
            "nightlife = club nights and parties; nature = outdoor, desert, beach, stargazing; "
            "market = markets held as events: flea, night, farmers', craft, winter and Christmas markets, bazaars (not venues that only have Market in their name); "
            "community = meetups, charity, national-day celebrations. "
            "If something is for children or families, always use family.")},
        "start_date": {"type": ["string", "null"], "description": "YYYY-MM-DD. Null if the page gives no date."},
        "end_date": {"type": ["string", "null"], "description": "YYYY-MM-DD for multi-day runs (exhibitions, festivals). Null otherwise."},
        "start_time": {"type": ["string", "null"], "description": "HH:MM 24h when the show/event itself STARTS. Never the doors-opening time. Null if not on the page."},
        "time_kind": {"type": "string", "enum": ["show_start", "doors_only", "none"], "description": "show_start if start_time is the real start; doors_only if the page gives only a doors-open time (then start_time must be null)."},
        "doors_time": {"type": ["string", "null"], "description": "HH:MM doors-open time if the page gives one."},
        "end_time": {"type": ["string", "null"]},
        "venue": {"type": ["string", "null"], "description": "Specific venue as written on the page, in English with normal capitalisation (translate an Arabic-only name). Null if not on the page."},
        "city": {"type": "string", "enum": CITIES},
        "price_text": {"type": ["string", "null"], "description": "Price as written, e.g. 'From AED 95'. Null if not on the page."},
        "price_min_aed": {"type": ["number", "null"], "description": "Lowest price in AED as a number. Null if not on the page."},
        "is_free": {"type": "boolean", "description": "True ONLY if the page says free / free entry / complimentary."},
        "kid_friendly": {"type": "boolean", "description": "True only if the page says it is for children or families."},
        "registration_required": {"type": "boolean"},
        "description": {"type": ["string", "null"], "description": "One or two short sentences written in YOUR OWN WORDS (never copy sentences from the page), only facts from the page."},
        "detail_url": {"type": ["string", "null"], "description": "URL of this event's own page, copied from the LINKS list. Null if none."},
        "organiser_url": {"type": ["string", "null"], "description": "Only for tourism-board sources: the organiser's own website or ticket page for this event, copied exactly from the EXTERNAL LINKS list. Null if none."},
        "evidence": {
            "type": "object",
            "description": "Exact verbatim snippets copied from PAGE TEXT that prove each field. Copy, do not paraphrase. Null when the field is null.",
            "properties": {
                "title": {"type": ["string", "null"]},
                "date": {"type": ["string", "null"]},
                "time": {"type": ["string", "null"]},
                "venue": {"type": ["string", "null"]},
                "price": {"type": ["string", "null"]},
            },
            "required": ["title", "date", "time", "venue", "price"],
        },
    },
    "required": [
        "title", "category", "start_date", "end_date", "start_time", "end_time", "venue", "city",
        "price_text", "price_min_aed", "is_free", "kid_friendly", "registration_required", "time_kind", "doors_time",
        "description", "detail_url", "organiser_url", "evidence",
    ],
}

TOOL = {
    "name": "save_events",
    "description": "Save the events found on the page.",
    "input_schema": {
        "type": "object",
        "properties": {
            "events": {"type": "array", "items": ITEM_SCHEMA},
            "rejected": {
                "type": "array",
                "description": "Things on the page that are NOT events under the entry rule, with a short reason.",
                "items": {
                    "type": "object",
                    "properties": {"title": {"type": "string"}, "reason": {"type": "string"}},
                    "required": ["title", "reason"],
                },
            },
        },
        "required": ["events", "rejected"],
    },
}

RULES = """You extract events for OutToday, an app that tells UAE residents where to go out.

ABSOLUTE RULES
- Use ONLY facts written in PAGE TEXT. Never guess, never use outside knowledge, never fill gaps with typical values.
- If a field is not on the page, set it to null. A null is always better than a guess.
- Every non-null field needs an exact verbatim quote from PAGE TEXT in "evidence". Copy characters exactly.
- Dates: today is {today}. If the page shows a day and month without a year, use the next occurrence on or after today. Skip events that have already ended.
- If one event lists several specific dates or sessions, output one item per date (max 12).
- Exhibitions and festivals that run over a period: one item with start_date and end_date.
- Times: start_time is when the show or event starts ("Show starts", "Starts", "Event time"). "Doors open" / "Doors" is NOT the start time: put it in doors_time. If the page gives only a doors time, start_time = null.
- Prices: only AED amounts written on the page. "Free" only if the page says so.
- detail_url must be copied exactly from the LINKS list.
- Default venue for this source (use ONLY when the page clearly describes events at this one place and names no other venue): {default_venue}
- Default city: {city}

ENTRY RULE (apply before saving)
Save only things that are a real reason to go out at a specific time: concerts, shows, performances, talks, screenings, workshops, festivals, exhibitions with dates, sports events, markets with dates.
Put into "rejected" (with reason): permanent collections or regular opening hours with no dates, generic infrastructure (paths, promenades, bridges, parks as such), events outside the UAE (e.g. a partner museum abroad), news articles and press releases about programmes, open calls / competitions / applications, trade-only or B2B shows, summits and conferences for professionals (keep consumer shows open to the public), online-only events, members-only or private events, school-only performances (school matinees for school groups), job ads, news articles, newsletters, shop products, gift cards, memberships, past events.
"""


class CollectOnly(Exception):
    """Pierwsze przejście trybu paczki: zapytanie zapisane, strona będzie przetworzona w drugim przejściu."""


# Tryb paczki (Batch API, 50% taniej): przejście 1 zbiera zapytania, paczka idzie do Anthropic,
# przejście 2 robi to samo co zwykle, ale bierze gotowe odpowiedzi z paczki.
BATCH: dict = {"mode": None, "requests": {}, "results": {}}
BATCH_WAIT_MIN = int(os.environ.get("BATCH_WAIT_MIN", "150"))


def run_batch(client) -> None:
    reqs = BATCH["requests"]
    if not reqs:
        return
    print(f"Paczka: {len(reqs)} zapytań do AI (Batch API, połowa ceny)")
    cachefix.guard()
    try:
        b = client.messages.batches.create(requests=[{"custom_id": k, "params": v} for k, v in reqs.items()])
    except Exception as e:
        print(f"   paczka niedostępna ({type(e).__name__}: {e}) – zwykłe zapytania")
        return
    t0 = time.time()
    while True:
        b = client.messages.batches.retrieve(b.id)
        if b.processing_status == "ended":
            break
        if time.time() - t0 > BATCH_WAIT_MIN * 60:
            print("   paczka nie skończyła się na czas – reszta zwykłymi zapytaniami")
            try:
                client.messages.batches.cancel(b.id)
            except Exception:
                pass
            break
        time.sleep(30)
    try:
        for r in client.messages.batches.results(b.id):
            if r.result.type == "succeeded":
                BATCH["results"][r.custom_id] = r.result.message
    except Exception as e:
        print(f"   wyniki paczki: {type(e).__name__}: {e}")
    print(f"   gotowe: {len(BATCH['results'])}/{len(reqs)} w {int((time.time() - t0) / 60)} min")


def call_model(client, text: str, links: list[tuple[str, str]], source: dict, page_url: str, focus: str | None, usage: dict,
               ext_links: list[tuple[str, str]] | None = None) -> dict:
    links_txt = "\n".join(f"[{label}] {href}" for label, href in links)
    ext_txt = "\n".join(f"[{label}] {href}" for label, href in (ext_links or []))
    # Reguły są stałe (prompt cache); zmienne wartości idą na początek wiadomości.
    rules = RULES.format(today="TODAY (given in CONTEXT)", default_venue="DEFAULT VENUE (given in CONTEXT)",
                         city="DEFAULT CITY (given in CONTEXT)")
    ctx = (f"CONTEXT: TODAY = {today_uae().isoformat()}; DEFAULT VENUE = {source.get('default_venue') or 'none'}; "
           f"DEFAULT CITY = {source.get('city', 'Abu Dhabi')}\n")
    task = (
        f"This is the page of one event. Return only the event titled: {focus!r} (one item per date if it has several dates)."
        if focus
        else "Return every event on this page."
    )
    msg = (
        ctx + f"SOURCE: {source['name']}\nPAGE URL: {page_url}\n\n{task}\n\n"
        f"=== PAGE TEXT ===\n{text[:MAX_TEXT]}\n=== END PAGE TEXT ===\n\n"
        f"=== LINKS ===\n{links_txt}\n=== END LINKS ==="
        + (f"\n\n=== EXTERNAL LINKS (organisers) ===\n{ext_txt}\n=== END EXTERNAL LINKS ===" if ext_txt else "")
    )
    params = {"model": MODEL, "max_tokens": 16000, "system": rules, "tools": [TOOL],
              "tool_choice": {"type": "tool", "name": "save_events"}, "messages": [{"role": "user", "content": msg}]}
    if BATCH["mode"] and not focus:
        cid = hashlib.sha1(msg.encode()).hexdigest()
        if BATCH["mode"] == "collect":
            BATCH["requests"][cid] = params
            raise CollectOnly()
        res = BATCH["results"].get(cid)
        if res is not None:  # wynik z paczki (połowa ceny)
            usage["input"] += round(res.usage.input_tokens / 2)
            usage["output"] += round(res.usage.output_tokens / 2)
            usage["calls"] += 1
            cachefix.add_cost(res.usage.input_tokens / 2, res.usage.output_tokens / 2)
            for block in res.content:
                if block.type == "tool_use":
                    return clean_output(block.input)
            return {"events": [], "rejected": []}
    for attempt in range(3):
        try:
            resp = client.messages.create(**params)
            break
        except Exception as e:
            print(f"   [AI błąd, próba {attempt + 1}] {type(e).__name__}: {e}")
            time.sleep(5 * (attempt + 1))
    else:
        return {"events": [], "rejected": [], "error": "AI niedostępne"}
    usage["input"] += resp.usage.input_tokens
    usage["output"] += resp.usage.output_tokens
    usage["calls"] += 1
    for block in resp.content:
        if block.type == "tool_use":
            return clean_output(block.input)
    return {"events": [], "rejected": []}


def _as_list(v) -> list:
    if isinstance(v, str):
        try:
            v = json.loads(v)
        except ValueError:
            return []
    return v if isinstance(v, list) else []


def clean_output(out) -> dict:
    """AI czasem zwraca listę jako tekst JSON. Naprawiamy to i odrzucamy śmieci."""
    if not isinstance(out, dict):
        return {"events": [], "rejected": []}
    events = []
    for e in _as_list(out.get("events")):
        if isinstance(e, str):
            try:
                e = json.loads(e)
            except ValueError:
                continue
        if isinstance(e, dict):
            if isinstance(e.get("evidence"), str):
                try:
                    e["evidence"] = json.loads(e["evidence"])
                except ValueError:
                    e["evidence"] = {}
            events.append(e)
    rejected = [r for r in _as_list(out.get("rejected")) if isinstance(r, dict)]
    return {"events": events, "rejected": rejected}


# ---------------------------------------------------------------- kontrola faktów


# Miejsca za granicą, które pojawiają się na stronach partnerów z ZEA (wystawy wyjazdowe, Biennale itp.).
ABROAD = re.compile(r"\b(irish museum|imma|dublin|ireland|london|paris|new york|venice|venezia|berlin|tokyo|beirut|cairo|"
                    r"riyadh|jeddah|doha|kuwait|muscat|bahrain|manama|amman|istanbul|mumbai|delhi|karachi|lahore|"
                    r"united kingdom|france|germany|italy|usa|india|pakistan|saudi arabia|qatar|oman|egypt|lebanon|jordan)\b")


def check_item(raw: dict, page_norm: str, link_urls: set[str], source: dict, page_url: str) -> tuple[dict | None, str]:
    """Zwraca (wpis, powód_odrzucenia). Każde pole bez potwierdzenia na stronie jest kasowane."""
    ev = raw.get("evidence") or {}
    title = (raw.get("title") or "").strip()
    if not title:
        return None, "brak tytułu"
    if re.search(r"school matinee|school performance|for schools only|schools only", norm(title)):
        return None, "tylko dla szkół"
    if re.search(r"\b(summit|conference|congress|forum|symposium for professionals|trade show|b2b)\b", norm(title)) and "symposium o" not in norm(title):
        return None, "wydarzenie branżowe (konferencja/szczyt)"
    if re.search(r"\b(online|webinar|zoom|virtual|livestream|live stream|hybrid)\b", norm(f"{title} {raw.get('venue') or ''}")):
        return None, "online (nie dodajemy)"
    if re.search(r"\b(investor|investors|vc|venture capital|founders|startup pitch|networking|b2b|speed dating|dating|singles|mingle)\b", norm(title)):
        return None, "networking/inwestorzy/randki (nie dla OutToday)"
    if ABROAD.search(norm(f"{raw.get('venue') or ''} {raw.get('area') or ''}")):
        return None, "poza ZEA (miejsce za granicą)"
    if not (quote_on_page(title, page_norm) or quote_on_page(ev.get("title"), page_norm)):
        return None, "tytułu nie ma na stronie (AI wymyśliło?)"

    item = {
        "title": title,
        "category": raw.get("category") if raw.get("category") in EVENT_CATEGORIES else "culture",
        "city": raw.get("city") if raw.get("city") in CITIES else source.get("city", "Abu Dhabi"),
        "description": None if copied_text(raw.get("description"), page_norm) else raw.get("description"),
        "kid_friendly": bool(raw.get("kid_friendly")),
        "registration_required": bool(raw.get("registration_required")),
        "evidence": {"page": page_url},
        "gaps": [],
    }

    # data
    sd, ed = parse_date(raw.get("start_date")), parse_date(raw.get("end_date"))
    dq = ev.get("date")
    if sd and quote_on_page(dq, page_norm) and date_matches_quote(sd, ed, dq):
        item["start_date"], item["end_date"] = sd, (ed if ed and ed >= sd else None)
        item["evidence"]["date"] = dq
    else:
        item["start_date"], item["end_date"] = None, None
        item["gaps"].append("date")

    # godzina
    st, et = parse_time(raw.get("start_time")), parse_time(raw.get("end_time"))
    tq = ev.get("time")
    doors_only = raw.get("time_kind") == "doors_only" or (
        tq and re.search(r"\bdoors?\b", norm(tq)) and not re.search(r"show|start|begin|perform|curtain", norm(tq))
    )
    dt_ = parse_time(raw.get("doors_time"))
    if dt_ and st == dt_:
        doors_only = True
    if st and not doors_only and quote_on_page(tq, page_norm) and time_matches_quote(st, tq):
        item["start_time"] = st
        item["end_time"] = et if et and time_matches_quote(et, tq) else None
        item["evidence"]["time"] = tq
    else:
        item["start_time"], item["end_time"] = None, None
        item["gaps"].append("start_time")

    # miejsce
    venue = (raw.get("venue") or "").strip() or None
    vq = ev.get("venue")
    default_venue = source.get("default_venue")
    if venue and quote_on_page(vq, page_norm):
        # sala w obiekcie (np. "Main Auditorium") -> "Main Auditorium, Dubai Opera, Downtown Dubai"
        if source.get("single_venue") and default_venue and not titles_match(venue, default_venue) \
                and not set(_tokens(default_venue.split(",")[0])) <= set(_tokens(venue)):
            venue = f"{venue}, {default_venue}"
        item["venue"] = venue
        item["evidence"]["venue"] = vq
    elif default_venue and (source.get("single_venue") or (venue and norm(venue) == norm(default_venue))):
        item["venue"] = default_venue
        item["evidence"]["venue"] = "domyślne miejsce źródła"
    else:
        item["venue"] = None
        item["gaps"].append("venue")

    # cena
    pq = ev.get("price")
    pmin = raw.get("price_min_aed")
    if raw.get("is_free") and quote_on_page(pq, page_norm) and re.search(r"\bfree\b|complimentary|no charge", norm(pq)):
        item.update(is_free=True, price_text="Free", price_min_aed=0)
        item["evidence"]["price"] = pq
    elif pmin is not None and quote_on_page(pq, page_norm) and number_in_quote(pmin, pq):
        item.update(is_free=False, price_text=clean_price(raw.get("price_text") or f"AED {pmin:g}"), price_min_aed=pmin)
        item["evidence"]["price"] = pq
    elif free_entry_applies(source, item.get("start_date"), item.get("end_date")):
        fe = source["free_entry"]
        item.update(is_free=True, price_text="Free entry", price_min_aed=0)
        item["evidence"]["price"] = f"{fe['quote']} ({fe['url']})"
    else:
        item.update(is_free=False, price_text=None, price_min_aed=None)
        item["gaps"].append("price")

    # link do strony eventu
    du = raw.get("detail_url")
    item["detail_url"] = du if du in link_urls else None
    item["evidence"]["title"] = ev.get("title") or title

    # minione
    end = item["end_date"] or item["start_date"]
    if end and end < today_uae():
        return None, "event już minął"
    return item, ""


def free_entry_applies(source: dict, sd, ed) -> bool:
    """Źródło ma na oficjalnej stronie 'wstęp wolny' (cytat + adres w sources/*.json).
    scope 'all' = każdy wpis bez ceny, 'exhibitions' = tylko wpisy z zakresem dat (wystawy w galeriach)."""
    fe = source.get("free_entry")
    if not fe:
        return False
    if fe.get("scope") == "all":
        return True
    return bool(sd and ed and str(ed) > str(sd))


def clean_price(t: str) -> str:
    """Nowy symbol dirhama bywa ikoną fontu (widać np. 'ê 60'). Zamieniamy na AED."""
    t = re.sub(r"\s+", " ", t.replace("\u20c3", "AED ")).strip()
    t = re.sub(r"(?<![A-Za-z])[êÊ\ue000-\uf8ff]\s*(?=\d)", "AED ", t)
    t = re.sub(r"AED(?=\d)", "AED ", t)
    return t.replace("  ", " ").replace(" • ", " · ").strip()


def copied_text(desc: str | None, page_norm: str, n: int = 7) -> bool:
    """Opis ma być naszymi słowami: 7 kolejnych słów identycznych ze stroną = kopia."""
    words = norm(desc).split()
    return any(" ".join(words[i:i + n]) in page_norm for i in range(0, max(0, len(words) - n + 1)))


def date_matches_quote(sd: dt.date, ed: dt.date | None, quote: str) -> bool:
    q = norm(quote)
    nums = {int(n) for n in re.findall(r"\d{1,4}", q)}

    def ok(d: dt.date) -> bool:
        full, short = MONTHS[d.month - 1]
        month_ok = full in q or re.search(rf"\b{short}\b", q) or d.month in nums
        return d.day in nums and bool(month_ok)

    return ok(sd) and (ed is None or ok(ed))


def time_matches_quote(t: str, quote: str) -> bool:
    h, m = int(t[:2]), int(t[3:])
    q = norm(quote)
    h12 = h % 12 or 12
    pats = [rf"\b0?{h}[:.]{m:02d}\b", rf"\b{h12}([:.]{m:02d})?\s*(am|pm|a\.m|p\.m)"]
    if m == 0:
        pats.append(rf"\b0?{h}\s*h\b")
    return any(re.search(p, q) for p in pats)


def number_in_quote(n: float, quote: str) -> bool:
    q = norm(quote).replace(",", "")
    return any(abs(float(x) - float(n)) < 0.01 for x in re.findall(r"\d+(?:\.\d+)?", q))


def bot_key(source_id: str, item: dict) -> str:
    raw = f"{source_id}|{norm(item['title'])}|{item.get('start_date')}|{item.get('start_time')}"
    return hashlib.sha1(raw.encode()).hexdigest()[:20]


# ---------------------------------------------------------------- Supabase


PROBATION_MIN, PROBATION_SHARE = 5, 0.4


def src_key(name: str | None) -> str:
    """Klucz źródła do oceny: konto Instagram osobno (@konto), reszta po nazwie źródła."""
    n = name or ""
    m = re.search(r"@([\w.]+)", n)
    return f"ig:{m.group(1).lower()}" if ("Instagram" in n and m) else n


class DB:
    def __init__(self, url: str, key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.h = {"apikey": key, "Content-Type": "application/json"}
        if not key.startswith("sb_"):  # stare klucze JWT potrzebują też nagłówka Authorization
            self.h["Authorization"] = f"Bearer {key}"

    @staticmethod
    def _retry(fn):
        """Odczyt i aktualizacja są bezpieczne do powtórzenia: przy chwilowym braku odpowiedzi z bazy próbujemy 3 razy."""
        for attempt in range(3):
            try:
                r = fn()
                if r.status_code < 500 or attempt == 2:
                    return r
            except (requests.Timeout, requests.ConnectionError):
                if attempt == 2:
                    raise
            time.sleep(5 * (attempt + 1))

    def get(self, table: str, params: dict) -> list:
        # Supabase zwraca max 1000 wierszy na zapytanie, więc pobieramy stronami
        want = int(params.get("limit", 1000))
        p = {k: v for k, v in params.items() if k != "limit"}
        if want > 1000 and "order" not in p and table in ("events", "places", "deals"):
            p["order"] = "id.asc"  # stała kolejność między stronami
        out, start = [], 0
        while start < want:
            end = min(start + 1000, want) - 1
            r = self._retry(lambda: requests.get(f"{self.base}/{table}", headers={**self.h, "Range": f"{start}-{end}"},
                                                 params=p, timeout=30))
            r.raise_for_status()
            page = r.json()
            out += page
            if len(page) < end - start + 1:
                break
            start = end + 1
        return out

    # --- REGUŁA (25.11.2026, decyzja właściciela): OCENA ŹRÓDEŁ ---
    # Źródło, z którego przy kontroli odrzucono co najmniej 40% ocenionych pozycji (minimum 5 ocenionych),
    # traci automatyczne zatwierdzanie: jego nowe pozycje czekają na przegląd (pending).
    # Liczone na bieżąco z bazy, więc źródło samo wraca do łask, gdy jego pozycje znów przechodzą kontrolę.
    guard = True  # manual_add wyłącza: ręczne wpisy są już sprawdzone

    def probation(self) -> set:
        if getattr(self, "_prob", None) is None:
            self._prob = set()
            try:
                import collections
                sc = collections.defaultdict(collections.Counter)
                for t in ("events", "deals"):
                    for r in self.get(t, {"select": "source_name,status", "status": "in.(approved,rejected)", "limit": "60000"}):
                        sc[src_key(r.get("source_name"))][r["status"]] += 1
                for k, c in sc.items():
                    judged = c["approved"] + c["rejected"]
                    if k and judged >= PROBATION_MIN and c["rejected"] / judged >= PROBATION_SHARE:
                        self._prob.add(k)
                if self._prob:
                    print(f"[ocena źródeł] bez automatycznego zatwierdzania: {len(self._prob)} źródeł")
            except Exception as e:  # ocena nie może zatrzymać bota
                print(f"[ocena źródeł] nie udało się policzyć ({e})")
        return self._prob

    def _guard(self, table: str, row: dict) -> dict:
        if self.guard and table in ("events", "deals") and row.get("status") == "approved" \
                and src_key(row.get("source_name")) in self.probation():
            row = {**row, "status": "pending"}
            row.pop("verified_at", None)
            if isinstance(row.get("evidence"), dict):
                row["evidence"] = {k: v for k, v in row["evidence"].items() if k != "auto"}
            print(f"   [ocena źródeł] {row.get('source_name')}: do przeglądu zamiast od razu do apki")
        return row

    def insert(self, table: str, rows: list | dict) -> list:
        rows = [self._guard(table, x) for x in rows] if isinstance(rows, list) else self._guard(table, rows)
        r = requests.post(f"{self.base}/{table}", headers={**self.h, "Prefer": "return=representation"}, json=rows, timeout=30)
        if r.status_code == 409 and "bot_key" in r.text:
            print(f"   już jest w bazie (bot_key), pomijam")
            return []
        if r.status_code >= 400:
            raise RuntimeError(f"insert {table}: {r.status_code} {r.text[:300]}")
        return r.json()

    def update(self, table: str, match: dict, values: dict) -> None:
        params = {k: f"eq.{v}" for k, v in match.items()}
        r = self._retry(lambda: requests.patch(f"{self.base}/{table}", headers=self.h, params=params, json=values, timeout=30))
        if r.status_code >= 400:
            raise RuntimeError(f"update {table}: {r.status_code} {r.text[:300]}")

    def upsert(self, table: str, row: dict, on: str) -> None:
        r = requests.post(
            f"{self.base}/{table}", headers={**self.h, "Prefer": "resolution=merge-duplicates"},
            params={"on_conflict": on}, json=row, timeout=30,
        )
        if r.status_code >= 400:
            raise RuntimeError(f"upsert {table}: {r.status_code} {r.text[:300]}")


def auto_ok(item: dict, source: dict) -> bool:
    """Bot sam zatwierdza wpis, gdy data i miejsce są pewne (potwierdzone cytatem z oficjalnego źródła).
    Brak ceny lub godziny nie blokuje: apka pokazuje wtedy "check the official page" (decyzja użytkownika 17.11)."""
    gaps = set(item.get("gaps") or []) - {"price", "start_time"}
    return not gaps


def to_row(item: dict, source: dict, key: str, now_iso: str) -> dict:
    return {
        "title": item["title"],
        "description": item.get("description"),
        "category": item["category"],
        "start_date": item["start_date"].isoformat(),
        "end_date": item["end_date"].isoformat() if item.get("end_date") else None,
        "start_time": item.get("start_time"),
        "end_time": item.get("end_time"),
        "venue": item.get("venue"),
        "city": item["city"],
        "price_text": item.get("price_text"),
        "price_min_aed": item.get("price_min_aed"),
        "is_free": item.get("is_free", False),
        "kid_friendly": item.get("kid_friendly", False),
        "registration_required": item.get("registration_required", False),
        "url": item.get("ticket_url") or item.get("organiser_url") or item.get("detail_url") or item["evidence"]["page"],
        "official_url": item.get("organiser_url") or item.get("detail_url") or item["evidence"]["page"],
        "source_name": source["name"],
        "source_url": item["evidence"]["page"],
        "status": "approved" if auto_ok(item, source) else "pending",
        "verified_at": now_iso if auto_ok(item, source) else None,
        "bot_key": key,
        "evidence": {**item["evidence"], **({"auto": True} if auto_ok(item, source) else {})},
        "gaps": item["gaps"],
        "last_seen_at": now_iso,
    }


STOP = {"the", "and", "with", "live", "in", "at", "of", "a", "an", "by", "presents", "abu", "dhabi", "show", "concert"}


def _tokens(s: str) -> list[str]:
    s = unicodedata.normalize("NFKD", norm(s))
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9 ]+", " ", s.replace("'s", ""))
    return s.split()


def titles_match(a: str, b: str) -> bool:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return False
    ja, jb = " ".join(ta), " ".join(tb)
    if ja == jb or (min(len(ja), len(jb)) >= 8 and (ja in jb or jb in ja)):
        return True
    sa, sb = {t for t in ta if t not in STOP}, {t for t in tb if t not in STOP}
    small, big = (sa, sb) if len(sa) <= len(sb) else (sb, sa)
    if small and small == big:
        return True
    if len(small) >= 2 and small <= big and len(big) <= len(small) + 4:
        return True
    return len(small) >= 3 and len(small & big) / len(small) >= 0.8


def link_for_title(title: str, links: list, page_url: str) -> str | None:
    """Darmowo (bez AI): link z tej samej strony, którego tekst pasuje do tytułu eventu,
    gdy model nie podał detail_url. Bez stron ogólnych (/, /events, /whats-on) i bez strony, z której czytamy."""
    base = (page_url or "").rstrip("/")
    hits = []
    for label, href in links:
        p = urlparse(href or "")
        if not href or href.rstrip("/") == base or p.path in ("", "/") or "#" in href:
            continue
        if re.search(r"/(event/list|shows|festival|events?|whats-on|calendar)/?$", p.path):
            continue
        lw = [w for w in _tokens(label or "") if w not in STOP]
        tw = [w for w in _tokens(title) if len(w) > 3 and w not in STOP]
        slug = p.path.lower()
        # tekst linku musi mieć min. 2 znaczące słowa, a adres musi zawierać słowo z tytułu (nie /tags/abu-dhabi)
        if len(lw) >= 2 and label and titles_match(label, title) and any(w in slug for w in tw) \
                and not re.search(r"/(tags?|category|topics?|author)/", slug):
            hits.append(href)
    hits = list(dict.fromkeys(hits))
    return hits[0] if len(hits) == 1 else None


def same_running(e: dict, it: dict) -> bool:
    """Ten sam trwający event (wystawa, pakiet, cykl) widziany kolejnego dnia z przesuniętą datą początku:
    ten sam tytuł, zakresy dat się nakładają i ten sam link albo to samo miejsce."""
    if not titles_match(e["title"], it["title"]):
        return False
    s1, e1 = e["start_date"], e.get("end_date") or e["start_date"]
    s2 = it["start_date"].isoformat()
    e2 = (it.get("end_date") or it["start_date"]).isoformat() if it.get("end_date") or it.get("start_date") else s2
    if not (s1 <= e2 and s2 <= e1) or (e1 == s1 and e2 == s2):
        return False
    urls = {u.rstrip("/") for u in (e.get("url"), e.get("official_url")) if u}
    new = {u.rstrip("/") for u in (it.get("ticket_url"), it.get("official_url"), it.get("url")) if u}
    venue_same = bool(e.get("venue") and it.get("venue") and titles_match(e["venue"], it["venue"]))
    return bool(urls & new) or venue_same


def dedupe(accepted: list[tuple[dict, dict]]) -> list[tuple[dict, dict]]:
    """Ten sam event z dwóch źródeł (np. Etihad Arena i Yas Island): zostaje pełniejszy wpis.
    Przy remisie wygrywa źródło wyżej na liście (strona samego miejsca)."""
    kept: list[tuple[dict, dict]] = []
    for src, it in accepted:
        dup = next((i for i, (_, k) in enumerate(kept)
                    if k["start_date"] == it["start_date"] and titles_match(k["title"], it["title"])), None)
        if dup is None:
            kept.append((src, it))
        elif len(it["gaps"]) < len(kept[dup][1]["gaps"]):
            kept[dup] = (src, it)
    return kept


# ---------------------------------------------------------------- główna pętla


RECHECK_DAYS = 3
EMPTY_RECHECK_DAYS = 30  # strony, które ciągle nic nie dają
DAILY_HOSTS = ("platinumlist", "feverup", "eventbrite", "meetup.com", "hopasports", "ticketmaster", "q-tickets",
               "coca-cola-arena", "etihadarena", "virginmegastore")


def is_daily(src: dict, url: str) -> bool:
    return bool(src.get("daily")) or any(h in url.lower() for h in DAILY_HOSTS)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true", help="nic nie zapisuje w bazie, tylko raport")
    ap.add_argument("--force", action="store_true", help="sprawdź strony nawet bez zmian")
    ap.add_argument("--only", default="", help="id źródeł po przecinku, np. louvre_ad,etihad_arena")
    ap.add_argument("--max-items", type=int, default=50, help="limit wpisów na całe uruchomienie (próba: 50)")
    ap.add_argument("--max-details", type=int, default=40, help="ile podstron eventów otworzyć na źródło")
    ap.add_argument("--cities", default="", help="tylko źródła z tych miast (po przecinku) – do równoległych przebiegów")
    args = ap.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print("Brak ANTHROPIC_API_KEY")
        return 1
    import anthropic
    client = anthropic.Anthropic(api_key=api_key, max_retries=6)

    db = None
    sb_url, sb_key = os.environ.get("SUPABASE_URL", "").strip(), os.environ.get("SUPABASE_SECRET_KEY", "").strip()
    if sb_url and sb_key:
        db = DB(sb_url, sb_key)
        global _DB
        _DB = db
    elif not args.dry_run:
        print("Brak SUPABASE_URL / SUPABASE_SECRET_KEY, a to nie jest próba (--dry-run)")
        return 1

    sources = []
    for path in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "sources", "*.json"))):
        with open(path, encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, dict) and isinstance(d.get("sources"), list):  # hotels.json / instagram.json mają inny format
                sources += d["sources"]
    sources_all = list(sources)
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    if only:
        sources = [s for s in sources if s["id"] in only]
    cities = {c.strip().lower() for c in args.cities.split(",") if c.strip()}
    if cities:
        sources = [s for s in sources if (s.get("city") or "").lower() in cities]
        print(f"Część: {', '.join(sorted(cities))} – źródeł {len(sources)}")

    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    usage = {"input": 0, "output": 0, "calls": 0, "searches": 0}
    report: list[dict] = []
    source_log: list[dict] = []
    accepted: list[tuple[dict, dict]] = []

    existing = []
    if db:
        since = (today_uae() - dt.timedelta(days=120)).isoformat()
        cols = "id,title,start_date,end_date,start_time,venue,price_text,price_min_aed,status,url,official_url"
        try:
            existing = db.get("events", {"select": cols + ",bot_key", "start_date": f"gte.{since}", "limit": "5000"})
        except Exception:
            if not args.dry_run:
                print("Brak kolumny bot_key: najpierw uruchom sql/12_bots.sql w Supabase")
                return 1
            try:
                existing = db.get("events", {"select": cols, "start_date": f"gte.{since}", "limit": "5000"})
            except Exception as e:
                print(f"[uwaga] nie mogę odczytać events ({e})")
        print(f"W bazie {len(existing)} eventów do porównania")

    global _BROWSER
    with Browser() as br:
        _BROWSER = br
        use_batch = os.environ.get("BATCH") == "force" or (os.environ.get("BATCH", "1") != "0" and not args.dry_run and not only)
        n_rep, n_log = len(report), len(source_log)
        for _pass in (["collect", "use"] if use_batch else [None]):
            BATCH["mode"] = _pass
            if _pass == "use":
                run_batch(client)
                del report[n_rep:], source_log[n_log:]
                accepted.clear()
            for src in sources:
                if len(accepted) >= args.max_items:
                    break
                for url in src["urls"]:
                    log = {"source": src["name"], "url": url, "status": "", "found": 0, "kept": 0}
                    source_log.append(log)
                    # Oszczędność: codziennie tylko sprzedawcy biletów i duże hale; reszta co RECHECK_DAYS dni.
                    if db and not args.force and not only and not is_daily(src, url):
                        try:
                            prev = db.get("bot_pages", {"select": "last_fetched_at", "url": f"eq.{url}"})
                            last = prev[0]["last_fetched_at"] if prev and prev[0].get("last_fetched_at") else None
                            # Strona, która 3 razy z rzędu nie dała żadnego eventu: sprawdzamy raz w miesiącu.
                            empty = search_cache_get(f"empty:{url}", days=3650)
                            every = EMPTY_RECHECK_DAYS if (empty or "").isdigit() and int(empty) >= 3 else RECHECK_DAYS
                            # newsletter wspomniał event w tym miejscu: sprawdź od razu (flaga z bot/newsletters.py)
                            if search_cache_get(f"due:{url}", days=14) == "1":
                                every = 0
                                log["due"] = True
                            if last and dt.datetime.fromisoformat(last.replace("Z", "+00:00")) > \
                                    dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=every, hours=-2):
                                log["status"] = f"sprawdzane co {every} dni (ostatnio {last[:10]})"
                                continue
                        except Exception:
                            pass
                    try:
                        ok, why = robots_allows(url)
                        if not ok:
                            log["status"] = why
                            print(f"- {src['name']}: {why}, pomijam")
                            continue
                        try:
                            page = br.fetch(url)
                        except Exception as e:
                            log["status"] = f"błąd pobierania: {type(e).__name__}"
                            print(f"- {src['name']}: {log['status']} {e}")
                            continue
                        text = page["text"] or ""
                        log["status"] = f"HTTP {page['status']}, {len(text)} znaków"
                        print(f"- {src['name']}: {log['status']}")
                        if page["status"] >= 400 or len(text) < 200:
                            log["status"] += " (pusta lub błąd)"
                            continue

                        h = hashlib.sha256(norm(page.get("full_text") or text).encode()).hexdigest()  # skrót z pełnej strony: bez fałszywych "zmian"
                        if db and not args.force:
                            try:
                                prev = db.get("bot_pages", {"select": "content_hash", "url": f"eq.{url}"})
                            except Exception:
                                prev = []
                            if prev and prev[0]["content_hash"] == h:
                                log["status"] += ", bez zmian od ostatniego razu (pomijam AI)"
                                print("   bez zmian, pomijam")
                                continue

                        links = clean_links(page["links"], page["final_url"])
                        link_urls = {u for _, u in links}
                        page_norm = norm(text)
                        ext = external_links(page["links"], page["final_url"]) if src.get("gov_tourism") else None
                        ext_urls = {u for _, u in (ext or [])}
                        out = call_model(client, text, links, src, page["final_url"], None, usage, ext)
                        log["ai"] = True
                        for rj in out.get("rejected", []):
                            report.append({"source": src["name"], "title": rj.get("title"), "action": f"odrzucone: {rj.get('reason')}"})

                        if len(out.get("events", [])) < 3:
                            hints = [f"{l} -> {u}" for l, u in links if re.search(r"what.?s on|event|calendar|programme|program|performances|exhibitions", (l + " " + u).lower())]
                            log["status"] += " | mało eventów; możliwe strony: " + "; ".join(hints[:6])
                        details_used = 0
                        for raw in out.get("events", []):
                            log["found"] += 1
                            item, why = check_item(raw, page_norm, link_urls, src, page["final_url"])
                            if item and raw.get("organiser_url") in ext_urls:
                                item["organiser_url"] = raw["organiser_url"]
                            if item and not item.get("detail_url"):
                                item["detail_url"] = link_for_title(item["title"], links, page["final_url"])
                            if not item:
                                report.append({"source": src["name"], "title": raw.get("title"), "action": f"odrzucone: {why}"})
                                continue
                            items = [item]
                            # brakuje czegoś? zajrzyj na podstronę eventu
                            if item["gaps"] and item["detail_url"] and details_used < args.max_details:
                                details_used += 1
                                time.sleep(PAUSE_SECONDS)
                                items = enrich_from_detail(br, client, item, src, usage)
                            for it in items:
                                if len(accepted) >= args.max_items:
                                    break
                                if not it.get("start_date"):
                                    report.append(row_for_report(src, it, "do uzupełnienia ręcznie: brak daty (nie trafia do bazy)"))
                                    continue
                                accepted.append((src, it))
                                log["kept"] += 1

                        if db and not args.dry_run:
                            db.upsert("bot_pages", {"url": url, "content_hash": h, "last_fetched_at": now_iso, "last_status": log["status"]}, "url")
                    except CollectOnly:
                        pass  # przejście 1 paczki: strona czeka na odpowiedź z paczki
                    except Exception as e:
                        log["status"] += f" | BŁĄD: {type(e).__name__}: {str(e)[:150]}"
                        print(f"   błąd: {e}")
                    time.sleep(PAUSE_SECONDS)
        BATCH["mode"] = None

    # zapis do bazy
    before = len(accepted)
    accepted = dedupe(accepted)
    if before != len(accepted):
        print(f"Duplikaty między źródłami: usunięto {before - len(accepted)}")
    # Cykliczne spotkania (np. co tydzień): tylko 3 najbliższe terminy w ciągu 35 dni, żeby nie zalać apki.
    accepted.sort(key=lambda p: p[1]["start_date"])
    per_title: dict[str, int] = {}
    capped = []
    horizon = dt.date.today() + dt.timedelta(days=35)
    for src, it in accepted:
        k = norm(it["title"])
        n = per_title.get(k, 0)
        if n >= 3 or (n >= 1 and it["start_date"] > horizon):
            continue
        per_title[k] = n + 1
        capped.append((src, it))
    if len(capped) != len(accepted):
        print(f"Cykliczne: pominięto {len(accepted) - len(capped)} dalszych terminów")
    accepted = capped
    counts = {"new": 0, "seen": 0, "changes": 0}
    done_keys: set[str] = set()
    for src, it in accepted:
        key = bot_key(src["id"], it)
        if key in done_keys:
            continue
        done_keys.add(key)
        match = next((e for e in existing if e.get("bot_key") == key), None) or next(
            (e for e in existing if e["start_date"] == it["start_date"].isoformat() and titles_match(e["title"], it["title"])), None
        ) or next((e for e in existing if same_running(e, it)), None)
        if not match:
            action = "nowy, zatwierdzony automatycznie" if auto_ok(it, src) else "nowy (pending)"
            if db and not args.dry_run:
                db.insert("events", to_row(it, src, key, now_iso))
                counts["new"] += 1
            report.append(row_for_report(src, it, action + (" [próba: nie zapisano]" if args.dry_run else "")))
            continue

        diffs = []
        # cena: porównujemy liczby, nie zapis ("From AED 150" = "Prices from AED 150")
        np_, op_ = it.get("price_min_aed"), match.get("price_min_aed")
        if np_ is not None and op_ is not None and abs(float(np_) - float(op_)) > 0.01:
            diffs.append(("price_text", match.get("price_text"), it.get("price_text")))
        nt, ot = it.get("start_time"), (match.get("start_time") or "")[:5] or None
        if nt and ot and nt != ot:
            diffs.append(("start_time", ot, nt))
        # miejsce: tylko gdy strona podaje inne konkretne miejsce (nie domyślne źródła)
        nv, ov = it.get("venue"), match.get("venue")
        if nv and ov and it["evidence"].get("venue") != "domyślne miejsce źródła":
            a, b = " ".join(_tokens(nv)), " ".join(_tokens(ov))
            if a not in b and b not in a and not titles_match(nv, ov):
                diffs.append(("venue", ov, nv))
        action = "już jest w bazie" + (f", ZMIANA: {', '.join(f'{f}: {o} -> {n}' for f, o, n in diffs)}" if diffs else "")
        if db and not args.dry_run:
            upd = {"last_seen_at": now_iso}
            if not match.get("bot_key"):
                upd["bot_key"] = key
            if match["status"] == "pending":  # niezatwierdzone można poprawić od razu i uzupełnić braki
                upd.update({f: n for f, _, n in diffs})
                fills = {f: it.get(f) for f in ("start_time", "end_time", "venue", "price_text", "price_min_aed")
                         if it.get(f) is not None and match.get(f) in (None, "")}
                if fills:
                    upd.update(fills)
                    upd["gaps"] = it["gaps"]
                    upd["evidence"] = it["evidence"]
                    if it.get("ticket_url"):
                        upd["url"] = it["ticket_url"]
                if auto_ok(it, src) and src_key(src["name"]) not in db.probation():
                    upd.update({"status": "approved", "verified_at": now_iso,
                                "evidence": {**it["evidence"], "auto": True}})
            else:
                for f, o, n in diffs:
                    # Miejsce: zgłaszamy tylko, gdy w apce go brakuje albo jest "do potwierdzenia".
                    # Inne nazwy tego samego miejsca (Space42 / Space 42, nazwa festiwalu zamiast miejsca) to szum.
                    if f == "venue" and o and "confirm" not in str(o).lower():
                        continue
                    ev_key = {"price_text": "price", "start_time": "time", "venue": "venue"}[f]
                    db.insert("bot_changes", {
                        "table_name": "events", "row_id": match["id"], "field": f,
                        "old_value": str(o), "new_value": str(n),
                        "evidence": it["evidence"].get(ev_key), "source_url": it["evidence"]["page"],
                    })
                    counts["changes"] += 1
            db.update("events", {"id": match["id"]}, upd)
            counts["seen"] += 1
        report.append(row_for_report(src, it, action))

    if db and not args.dry_run:
        counts["auto_old"] = auto_approve_pending(db, sources_all, now_iso)
        from apply_changes import apply_safe_changes
        counts["auto_changes"] = apply_safe_changes(db)
    if db and not args.dry_run:
        # licznik "pustych" odczytów strony (AI nie znalazło żadnego eventu); zeruje się, gdy coś znajdzie
        for lg in source_log:
            if lg.get("due"):
                search_cache_put(f"due:{lg['url']}", "0")
            if lg.get("ai"):
                prev = search_cache_get(f"empty:{lg['url']}", days=3650) or "0"
                n = (int(prev) + 1) if lg["found"] == 0 and prev.isdigit() else 0
                search_cache_put(f"empty:{lg['url']}", str(n))
    write_report(report, source_log, usage, counts, args.dry_run)
    if db and not args.dry_run:
        db.insert("bot_runs", {"dry_run": False, "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                               "summary": {"usage": usage, "counts": counts, "sources": source_log}})
    return 0


def auto_approve_pending(db: "DB", sources: list[dict], now_iso: str) -> int:
    """Wpisy z bota, które czekają, a spełniają zasadę automatycznego zatwierdzenia (np. sprzed wprowadzenia tej zasady)."""
    by_name = {s["name"]: s for s in sources}
    rows = db.get("events", {"select": "id,source_name,start_date,end_date,gaps,evidence",
                             "status": "eq.pending", "bot_key": "not.is.null", "limit": "2000"})
    n = 0
    for r in rows:
        src = by_name.get(r.get("source_name") or "")
        item = {"gaps": r.get("gaps") or [], "start_date": r["start_date"], "end_date": r.get("end_date")}
        if not src:
            continue
        upd: dict = {}
        ev = r.get("evidence") or {}
        if "price" in item["gaps"] and free_entry_applies(src, r["start_date"], r.get("end_date")):
            fe = src["free_entry"]
            item["gaps"] = [g for g in item["gaps"] if g != "price"]
            ev["price"] = f"{fe['quote']} ({fe['url']})"
            upd.update(price_text="Free entry", is_free=True, price_min_aed=0, gaps=item["gaps"], evidence=ev)
        if auto_ok(item, src) and src_key(src["name"]) not in db.probation():
            ev["auto"] = True
            upd.update(status="approved", verified_at=now_iso, evidence=ev)
            n += 1
        if upd:
            upd["updated_at"] = now_iso
            db.update("events", {"id": r["id"]}, upd)
    if n:
        print(f"Zatwierdzone automatycznie spośród czekających: {n}")
    return n


TICKET_SEARCH_DOMAINS = ["platinumlist.net", "district.ae", "livenation.me", "ticketmaster.ae", "coca-cola-arena.com",
                         "dubaiopera.com", "q-tickets.com", "800tickets.com", "ticketsmarche.com"]


def search_ticket_page(client, item: dict, src: dict, usage: dict) -> list[str]:
    """Strona eventu nie linkuje sprzedawcy biletów wprost: szukamy go (tylko domeny sprzedawców, ok. 0,01 USD).
    Wynik (także "nie znaleziono") pamiętamy 30 dni, żeby nie płacić drugi raz za to samo."""
    when = item["start_date"].isoformat() if item.get("start_date") else ""
    ckey = "tickets:" + hashlib.sha1(f"{norm(item['title'])}|{when}".encode()).hexdigest()[:20]
    cached = search_cache_get(ckey)
    if cached is not None:
        return [cached] if cached else []
    if not search_budget():
        return []
    prompt = (f"Find the ticket sale page for this exact event: {item['title']}, {when}, at {item.get('venue') or src['name']}, UAE. "
              "Answer with ONE line of JSON only: {\"url\": \"https://...\" or null}")
    try:
        resp = client.messages.create(
            model=MODEL, max_tokens=800,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2, "allowed_domains": TICKET_SEARCH_DOMAINS}],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        print(f"   [szukanie biletów] {e}")
        return []
    usage["input"] += resp.usage.input_tokens
    usage["output"] += resp.usage.output_tokens
    usage["calls"] += 1
    usage["searches"] = usage.get("searches", 0) + int(getattr(getattr(resp.usage, "server_tool_use", None), "web_search_requests", 0) or 0)
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    m = re.search(r"https?://[^\s\"'<>]+", text)
    url = m.group(0).rstrip(".,)") if m else ""
    if url and not any(d in urlparse(url).netloc.lower() for d in TICKET_SEARCH_DOMAINS):
        url = ""
    search_cache_put(ckey, url)
    return [url] if url else []


def enrich_from_tickets(br: "Browser", client, item: dict, src: dict, usage: dict, links: list) -> dict:
    """Brakuje godziny albo ceny? Sprawdź oficjalnego sprzedawcę biletów podlinkowanego na stronie eventu."""
    tl = ticket_links(links) or search_ticket_page(client, item, src, usage)
    print(f"   bilety dla '{item['title'][:40]}': {tl[:2]}")
    for url in tl:
        ok, _ = robots_allows(url)
        if not ok:
            continue
        try:
            time.sleep(PAUSE_SECONDS)
            page = br.fetch(url)
        except Exception:
            continue
        if page["status"] >= 400 or not page["text"]:
            continue
        out = call_model(client, page["text"], [], src, page["final_url"], item["title"], usage)
        pn = norm(page["text"])
        for raw in out.get("events", []):
            d, _ = check_item(raw, pn, set(), src, page["final_url"])
            if not d or d.get("start_date") != item.get("start_date"):
                continue
            merged = dict(item)
            merged["evidence"] = dict(item["evidence"])
            for fields, gap, evk in ((("start_time", "end_time"), "start_time", "time"),
                                     (("price_text", "price_min_aed", "is_free"), "price", "price")):
                if gap in merged["gaps"] and gap not in d["gaps"]:
                    for f in fields:
                        merged[f] = d[f]
                    merged["evidence"][evk] = d["evidence"].get(evk)
                    merged["evidence"][evk + "_page"] = page["final_url"]
                    merged["gaps"] = [g for g in merged["gaps"] if g != gap]
            merged["ticket_url"] = page["final_url"]
            return merged
    return item


def enrich_from_detail(br: Browser, client, item: dict, src: dict, usage: dict) -> list[dict]:
    url = item["detail_url"]
    ok, _ = robots_allows(url)
    if not ok:
        return [item]
    try:
        page = br.fetch(url)
    except Exception:
        return [item]
    if page["status"] >= 400 or not page["text"]:
        return [item]
    links = clean_links(page["links"], page["final_url"])
    ext = external_links(page["links"], page["final_url"]) if src.get("gov_tourism") else None
    ext_urls = {u for _, u in (ext or [])}
    out = call_model(client, page["text"], links, src, page["final_url"], item["title"], usage, ext)
    page_norm = norm(page["text"])
    results = []
    for raw in out.get("events", []):
        d, _ = check_item(raw, page_norm, {u for _, u in links}, src, page["final_url"])
        if not d:
            continue
        merged = dict(item)
        merged["evidence"] = dict(item["evidence"])
        merged["gaps"] = []
        for field, gap, evk in (
            (("start_date", "end_date"), "date", "date"),
            (("start_time", "end_time"), "start_time", "time"),
            (("venue",), "venue", "venue"),
            (("price_text", "price_min_aed", "is_free"), "price", "price"),
        ):
            if gap in item["gaps"] and gap not in d["gaps"]:
                for f in field:
                    merged[f] = d[f]
                merged["evidence"][evk] = d["evidence"].get(evk)
                merged["evidence"][evk + "_page"] = page["final_url"]
            if gap in item["gaps"] and gap in d["gaps"]:
                merged["gaps"].append(gap)
        if raw.get("organiser_url") in ext_urls:
            merged["organiser_url"] = raw["organiser_url"]
        if d.get("description") and not merged.get("description"):
            merged["description"] = d["description"]
        results.append(merged)
    results = results or [item]
    return [enrich_from_tickets(br, client, r, src, usage, page["links"])
            if src.get("trusted") and ({"start_time", "price"} & set(r["gaps"])) else r for r in results]


def row_for_report(src: dict, it: dict, action: str) -> dict:
    ev = it.get("evidence", {})
    return {
        "source": src["name"],
        "title": it.get("title"),
        "category": it.get("category"),
        "start_date": it.get("start_date"),
        "end_date": it.get("end_date"),
        "start_time": it.get("start_time"),
        "venue": it.get("venue"),
        "price": it.get("price_text"),
        "free": "tak" if it.get("is_free") else "",
        "gaps": ", ".join(it.get("gaps", [])),
        "link": it.get("organiser_url") or it.get("detail_url") or ev.get("page"),
        "evidence_date": ev.get("date"),
        "evidence_price": ev.get("price"),
        "action": action,
    }


def write_report(report, source_log, usage, counts, dry_run) -> None:
    os.makedirs("out", exist_ok=True)
    fields = ["source", "title", "category", "start_date", "end_date", "start_time", "venue", "price",
              "free", "gaps", "link", "evidence_date", "evidence_price", "action"]
    with open("out/report.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in report:
            w.writerow(r)

    kept = [r for r in report if not str(r["action"]).startswith("odrzucone")]
    lines = [
        f"# OutToday bot: {'PRÓBA (nic nie zapisano)' if dry_run else 'zapis do bazy'}",
        "",
        f"Wywołania AI: {usage['calls']}, tokeny: {usage['input']} wejście / {usage['output']} wyjście",
        f"Wpisy: {len(kept)} przyjęte, {len(report) - len(kept)} odrzucone. "
        + ("" if dry_run else f"Nowe w bazie: {counts['new']}, już były: {counts['seen']}, zmiany do sprawdzenia: {counts['changes']}, "
                              f"zatwierdzone automatycznie spośród czekających: {counts.get('auto_old', 0)}"),
        "",
        "## Źródła",
        "| Źródło | Status | Znalezione | Przyjęte |",
        "|---|---|---|---|",
    ]
    for s in source_log:
        lines.append(f"| {s['source']} | {s['status']} | {s['found']} | {s['kept']} |")
    lines += ["", "## Wpisy", "| Tytuł | Data | Godz. | Miejsce | Cena | Braki | Co zrobiono |", "|---|---|---|---|---|---|---|"]
    for r in report:
        cell = lambda v: str(v or "").replace("|", "/")[:80]
        date = cell(r.get("start_date")) + (f" – {cell(r.get('end_date'))}" if r.get("end_date") else "")
        lines.append(f"| {cell(r.get('title'))} | {date} | {cell(r.get('start_time'))} | {cell(r.get('venue'))} | "
                     f"{cell(r.get('price'))} | {cell(r.get('gaps'))} | {cell(r.get('action'))} |")
    md = "\n".join(lines) + "\n"
    with open("out/summary.md", "w", encoding="utf-8") as f:
        f.write(md)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(md)
    print(md)


if __name__ == "__main__":
    sys.exit(main())
