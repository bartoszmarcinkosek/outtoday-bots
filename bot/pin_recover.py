"""Odzyskiwanie pinezek usuniętych przez pin_verify.py (decyzja właściciela 27.11.2026: pinezka tylko prawidłowa).
Pinezka wraca, gdy DWA niezależne źródła (OpenStreetMap i Google) wskazują to samo miejsce dla pełnej nazwy
– wtedy wpisujemy punkt Google (stara pinezka była błędna). Brak zgody źródeł = dalej bez pinezki (mapy szukają po nazwie).
Uruchomienie: python bot/pin_recover.py [--apply]"""
from __future__ import annotations
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402
import geocode as G  # noqa: E402
from pin_verify import BIG, BLOCK  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--apply", action="store_true"); a = ap.parse_args()
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    cache = json.load(open(G.CACHE, encoding="utf-8")) if os.path.exists(G.CACHE) else {}
    blocked = json.load(open(BLOCK, encoding="utf-8")) if os.path.exists(BLOCK) else {}
    back = still = 0
    for key in list(blocked):
        venue, _, city = key.rpartition("|")
        if not venue or city not in G.CITY:
            still += 1; continue
        big = bool(BIG.search(venue))
        best = None
        for q in ([f"{venue}, {city}" if city.lower() not in venue.lower() else venue, f"{venue}, {city}, United Arab Emirates"]):
            osm = G.lookup(q, cache); ggl = G.lookup_google(q, cache)
            if osm and ggl and G.km(osm, ggl) * 1000 <= (1500 if big else 400) \
                    and G.km(ggl, G.CITY[city]) <= 90:
                best = ggl; break
        if not best:
            still += 1; print(f"PR|STILL|{city}|{venue}"); continue
        back += 1; print(f"PR|BACK|{city}|{venue}|{best[0]:.5f},{best[1]:.5f}")
        if a.apply:
            for table, col in (("events", "venue"), ("places", "name"), ("deals", "venue")):
                for r in db.get(table, {"select": "id", col: f"eq.{venue}", "city": f"eq.{city}", "lat": "is.null", "limit": "500"}):
                    db.update(table, {"id": r["id"]}, {"lat": best[0], "lng": best[1]})
            del blocked[key]
    json.dump(cache, open(G.CACHE, "w", encoding="utf-8"), ensure_ascii=False)
    if a.apply:
        json.dump(blocked, open(BLOCK, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
    print(f"PR|SUMMARY|wróciło {back}|dalej bez pinezki {still}|google {G._g_used}|apply {a.apply}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
