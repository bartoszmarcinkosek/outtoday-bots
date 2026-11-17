"""OutToday: współrzędne z OFICJALNYCH stron (link "Get directions", mapa na stronie, dane schema.org).

Dla wpisów bez lat/lng otwiera ich official_url (bez AI) i szuka współrzędnych podanych przez sam lokal
lub sprzedawcę biletów: linki Google/Apple Maps i Waze z liczbami, osadzona mapa, schema.org "geo", geo:...
Bierze wynik tylko gdy na stronie jest dokładnie JEDNO miejsce (strony z listą wielu hoteli pomija)
i gdy punkt leży w ZEA, nie dalej niż 70 km od środka miasta wpisu. Nie korzysta z usług Google.

Uruchomienie: python bot/geo_pages.py [--limit 800] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from urllib.parse import unquote, urlparse

import requests

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402
from geocode import CITY, km  # noqa: E402

CACHE = os.path.join(os.path.dirname(__file__), "..", "sources", "pagegeo_cache.json")
SKIP_HOSTS = ("instagram.com", "facebook.com", "meetup.com", "forms.gle", "google.com", "goo.gl", "tiktok.com", "x.com")
NUM = r"(-?\d{1,2}\.\d{3,})"
PATTERNS = [
    re.compile(r"@" + NUM + r"," + NUM + r",\d"),                         # google.com/maps/@lat,lng,17z
    re.compile(r"[?&](?:q|ll|sll|daddr|destination|query|center)=" + NUM + r"(?:,|%2C)\s*" + NUM),
    re.compile(r"!3d" + NUM + r"!4d" + NUM),                              # google ...!3dLAT!4dLNG
    re.compile(r"geo:" + NUM + r"," + NUM),
    re.compile(r'"latitude"\s*:\s*"?' + NUM + r'"?\s*,\s*"longitude"\s*:\s*"?' + NUM),
    re.compile(r'data-lat(?:itude)?="' + NUM + r'"[^>]{0,200}?data-(?:lng|lon|longitude)="' + NUM),
    re.compile(r'(?:place:location|og):latitude"\s+content="' + NUM + r'"[\s\S]{0,200}?longitude"\s+content="' + NUM),
]
EMBED = re.compile(r"!2d" + NUM + r"!3d" + NUM)                            # embed: !2dLNG!3dLAT


def coords_in(html: str) -> list[tuple[float, float]]:
    text = unquote(html.replace("&amp;", "&"))
    pts = []
    for p in PATTERNS:
        pts += [(float(a), float(b)) for a, b in p.findall(text)]
    pts += [(float(b), float(a)) for a, b in EMBED.findall(text)]
    return [(a, b) for a, b in pts if 22.5 <= a <= 26.5 and 51.0 <= b <= 56.6]  # tylko ZEA


def one_place(pts: list[tuple[float, float]]) -> tuple[float, float] | None:
    if not pts:
        return None
    first = pts[0]
    if all(km(first, p) <= 0.6 for p in pts):
        return first
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=800, help="ile stron otworzyć")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    today = R.today_uae().isoformat()
    rows = []
    for table, name_col in (("events", "venue"), ("places", "name"), ("deals", "venue")):
        q = {"select": f"id,{name_col},city,official_url", "lat": "is.null", "status": "eq.approved",
             "official_url": "not.is.null", "limit": "5000"}
        if table == "events":
            q["or"] = f"(end_date.gte.{today},start_date.gte.{today})"
        rows += [(table, r) for r in db.get(table, q)]
    by_url: dict[str, list] = {}
    for table, r in rows:
        u = (r.get("official_url") or "").strip()
        host = urlparse(u).netloc.lower()
        if u.startswith("http") and not any(h in host for h in SKIP_HOSTS) and r.get("city") in CITY:
            by_url.setdefault(u, []).append((table, r))
    print(f"Wpisów bez współrzędnych z oficjalnym linkiem: {sum(len(v) for v in by_url.values())}, stron: {len(by_url)}")
    opened = found = updated = 0
    last_host: dict[str, float] = {}
    for url, items in by_url.items():
        if url in cache:
            hit = cache[url]
        else:
            if opened >= a.limit:
                continue
            ok, why = R.robots_allows(url)
            if not ok:
                cache[url] = None
                continue
            host = urlparse(url).netloc
            wait = 1.5 - (time.time() - last_host.get(host, 0))
            if wait > 0:
                time.sleep(wait)
            last_host[host] = time.time()
            opened += 1
            try:
                resp = requests.get(url, headers={"User-Agent": R.USER_AGENT}, timeout=30)
                hit = one_place(coords_in(resp.text)) if resp.status_code < 400 else None
            except Exception:
                hit = None
            cache[url] = list(hit) if hit else None
        if not hit:
            continue
        found += 1
        for table, r in items:
            if km(tuple(hit), CITY[r["city"]]) > 70:
                continue
            print(f"{table:6} {(r.get('venue') or r.get('name') or '')[:45]:45} {r['city']:14} -> {hit[0]:.5f},{hit[1]:.5f}")
            if not a.dry_run:
                db.update(table, {"id": r["id"]}, {"lat": round(hit[0], 6), "lng": round(hit[1], 6)})
            updated += 1
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"Otwarte strony: {opened}. Strony ze współrzędnymi: {found}. Uzupełnione wpisy: {updated}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
