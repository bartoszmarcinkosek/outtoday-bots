"""OutToday: zamienia nazwy miejsc na współrzędne (OpenStreetMap / Nominatim) dla eventów, miejsc i ofert.

Zasady Nominatim: max 1 zapytanie na sekundę, własny User-Agent, wyniki zapisane w pamięci podręcznej
(sources/geo_cache.json), więc to samo miejsce nigdy nie jest pytane drugi raz.
Wynik musi leżeć w ZEA i nie dalej niż 70 km od środka miasta wpisu; inaczej zostaje bez współrzędnych.
Uruchomienie: python bot/geocode.py [--limit 1500]
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402

CACHE = os.path.join(os.path.dirname(__file__), "..", "sources", "geo_cache.json")
UA = "OutToday-app/1.0 (UAE events app; contact outtodayapp.uae@gmail.com)"
CITY = {"Dubai": (25.20, 55.27), "Abu Dhabi": (24.45, 54.38), "Al Ain": (24.21, 55.74), "Sharjah": (25.34, 55.41),
        "Ajman": (25.40, 55.48), "Ras Al Khaimah": (25.79, 55.94), "Fujairah": (25.13, 56.33), "Umm Al Quwain": (25.56, 55.55)}
VAGUE = re.compile(r"^(various|multiple|online|virtual|tbc|tba|-|uae|dubai|abu dhabi|sharjah|ajman|fujairah|al ain|"
                   r"ras al khaimah|umm al quwain|united arab emirates)\s*(region|desert|city|emirate)?\s*$|various venues|across (the )?(city|emirate|uae)", re.I)


def km(a, b):
    r = math.radians
    d = math.sin(r(b[0] - a[0]) / 2) ** 2 + math.cos(r(a[0])) * math.cos(r(b[0])) * math.sin(r(b[1] - a[1]) / 2) ** 2
    return 6371 * 2 * math.asin(math.sqrt(d))


# Nazwy, pod którymi OpenStreetMap zna miejsca (nazwa w ogłoszeniach -> nazwa w OSM)
ALIAS = [
    (r"adnec centre al ain|adnec al ain|al ain convention", "Al Ain Convention Centre"),
    (r"al ain oasis", "Al Ain Oasis"),
    (r"jahili", "Al Jahili Fort"),
    (r"qattara", "Al Qattara Oasis"),
    (r"al ain rotana", "Al Ain Rotana"),
    (r"al ain palace", "Al Ain Palace Hotel"),
    (r"radisson blu.*al ain", "Radisson Blu Hotel & Resort, Al Ain"),
    (r"hili fun city", "Hili Fun City"),
    (r"al ain zoo", "Al Ain Zoo"),
    (r"jebel hafeet|jabal hafeet|jebel hafit", "Jebel Hafeet"),
    (r"green mubazzarah|mubazzarah", "Green Mubazzarah"),
    (r"telal resort", "Telal Resort"),
]


def candidates(venue: str, city: str) -> list[str]:
    v = re.sub(r"\s+", " ", venue).strip(" ,")
    parts = [p.strip() for p in v.split(",") if p.strip()]
    out = [f"{name}, Al Ain" if "Al Ain" not in name else name for rx, name in ALIAS if re.search(rx, v, re.I)]
    out += [f"{v}, {city}"]
    if len(parts) > 1:  # "Outlet, Hotel" -> spróbuj samego hotelu / ostatniej części
        out += [f"{parts[-1]}, {city}", f"{parts[0]}, {city}"]
    # zbyt ogólne zapytania (samo miasto/kraj/dzielnica) dają środek miasta zamiast miejsca – nie używamy ich
    return [q for q in dict.fromkeys(out) if not too_generic(q.rsplit(",", 1)[0], city)]


GENERIC = {"ae", "uae", "united arab emirates", "dubai", "abu dhabi", "sharjah", "ajman", "ras al khaimah", "rak",
           "fujairah", "umm al quwain", "al ain", "outdoor area", "various locations", "multiple locations", "tbc", "tba",
           "downtown", "downtown dubai", "dubai marina", "saadiyat island", "yas island", "jlt", "al marjan island"}


def too_generic(head: str, city: str) -> bool:
    h = re.sub(r"[^a-z ]", "", head.lower()).strip()
    return h in GENERIC or h == city.lower() or len(h) < 3


def lookup(q: str, cache: dict) -> list | None:
    if q in cache:
        return cache[q]
    time.sleep(1.1)
    try:
        r = requests.get("https://nominatim.openstreetmap.org/search",
                         params={"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "ae"},
                         headers={"User-Agent": UA}, timeout=30)
        res = r.json() if r.status_code == 200 else None
    except (requests.RequestException, ValueError):
        return None
    if res is None:  # błąd serwera / blokada – nie zapamiętujemy, spróbujemy następnej nocy
        return None
    cache[q] = [float(res[0]["lat"]), float(res[0]["lon"])] if res else []
    return cache[q]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=1500)
    a = ap.parse_args()
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    cache = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
    today = R.today_uae().isoformat()
    jobs = []
    for table, name_col, extra in (("events", "venue", {"end_date": f"gte.{today}"}), ("places", "name", {}), ("deals", "venue", {})):
        q = {"select": f"id,{name_col},city,lat", "lat": "is.null", "status": "neq.rejected", "limit": "5000"}
        if table == "events":
            q["or"] = f"(end_date.gte.{today},start_date.gte.{today})"
        rows = db.get(table, q)
        jobs += [(table, r["id"], r.get(name_col) or "", r.get("city") or "") for r in rows]
    print(f"Bez współrzędnych: {len(jobs)}")
    done = miss = 0
    for table, rid, venue, city in jobs[: a.limit]:
        if not venue or VAGUE.search(venue.strip()) or city not in CITY:
            miss += 1
            continue
        hit = None
        for q in candidates(venue, city):
            res = lookup(q, cache)
            if res and km(res, CITY[city]) <= 70:
                hit = res
                break
        if not hit:
            miss += 1
            continue
        db.update(table, {"id": rid}, {"lat": round(hit[0], 6), "lng": round(hit[1], 6)})
        done += 1
        if done % 50 == 0:
            json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
            print(f"... {done} gotowe", flush=True)
    json.dump(cache, open(CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    print(f"\nZ współrzędnymi: {done}. Nie znaleziono / zbyt ogólne: {miss}. Pamięć podręczna: {len(cache)} zapytań.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
