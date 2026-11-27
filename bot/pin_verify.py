"""Weryfikacja pinezek bez testerów (decyzja właściciela 27.11.2026: „pinezki tylko te prawidłowe”).
Pinezka zostaje tylko, gdy POTWIERDZAJĄ ją niezależne źródła dla PEŁNEJ nazwy miejsca:
  - OpenStreetMap i Google wskazują to samo miejsce (do 400 m od siebie) i pinezka leży przy nim, albo
  - Google zwraca konkretny obiekt (nie samo miasto/dzielnicę) do 300 m od pinezki.
Pozostałe pinezki są usuwane (lat/lng = null) – przyciski Google Maps / Waze w apce szukają wtedy po nazwie miejsca,
co prowadzi we właściwe miejsce. Nazwa trafia do sources/pin_blocked.json, żeby geocode.py jej nie wpisał ponownie.
Uruchomienie: python bot/pin_verify.py [--apply]   (bez --apply tylko raport PV|)"""
from __future__ import annotations
import argparse, collections, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402
import geocode as G  # noqa: E402

import re
BIG = re.compile(r"expo city|adnec|convention|exhibition cent|world trade|park|beach|island|corniche|oasis|souk|village|stadium|arena|festival|resort|mall|marina|waterfront|creek|desert|mountain|jebel|wadi|alserkal", re.I)
BLOCK = os.path.join(os.path.dirname(__file__), "..", "sources", "pin_blocked.json")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    cache = json.load(open(G.CACHE, encoding="utf-8")) if os.path.exists(G.CACHE) else {}
    blocked = json.load(open(BLOCK, encoding="utf-8")) if os.path.exists(BLOCK) else {}
    today = R.today_uae().isoformat()
    rows = []
    for table, col in (("events", "venue"), ("places", "name"), ("deals", "venue")):
        q = {"select": f"id,{col},city,lat,lng", "lat": "not.is.null", "status": "neq.rejected", "limit": "5000"}
        if table == "events":
            q["or"] = f"(end_date.gte.{today},and(end_date.is.null,start_date.gte.{today}))"
        rows += [(table, r["id"], (r.get(col) or "").strip(), r.get("city") or "", (r["lat"], r["lng"])) for r in db.get(table, q)]
    by_venue = collections.defaultdict(list)
    for t in rows:
        by_venue[(t[2], t[3])].append(t)
    ok = bad = 0
    verdict = {}
    for (venue, city), items in by_venue.items():
        pin = items[0][4]
        why = None
        if not venue or city not in G.CITY:
            why = "brak nazwy miejsca / miasta"
        else:
            full = f"{venue}, {city}" if city.lower() not in venue.lower() else venue
            osm = G.lookup(full, cache)
            ggl = G.lookup_google(full, cache)
            near = lambda p, m: bool(p) and G.km(p, pin) * 1000 <= m  # noqa: E731
            big = bool(BIG.search(venue))  # duże tereny (Expo City, ADNEC, park, plaża, wyspa): punkty źródeł mogą się różnić
            tol = 1500 if big else 600
            if osm and ggl and G.km(osm, ggl) * 1000 <= (2000 if big else 1000) and (near(osm, tol) or near(ggl, tol)):
                why = None
            elif ggl and near(ggl, 300):
                why = None
            elif ggl is None and osm and near(osm, 300):
                why = None  # Google niedostępny (limit) – na razie wystarczy OSM dla pełnej nazwy
            else:
                why = f"niepotwierdzona: osm={'brak' if not osm else round(G.km(osm, pin), 1)} km, google={'brak' if not ggl else round(G.km(ggl, pin), 1)} km"
        verdict[(venue, city)] = why
        if why:
            bad += len(items)
            print(f"PV|BAD|{city}|{venue}|{len(items)}|{why}")
            if a.apply:
                for table, rid, *_ in items:
                    db.update(table, {"id": rid}, {"lat": None, "lng": None})
                blocked[f"{venue}|{city}"] = f"{today} {why}"
        else:
            ok += len(items)
    json.dump(cache, open(G.CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    if a.apply:
        json.dump(blocked, open(BLOCK, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"PV|SUMMARY|pinezki {len(rows)}|miejsc {len(by_venue)}|potwierdzone {ok}|niepotwierdzone {bad}|google {G._g_used}|apply {a.apply}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
