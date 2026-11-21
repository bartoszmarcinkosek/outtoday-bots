"""Poprawa współrzędnych BEZ AI (koszt 0): usuwa pinezki ustawione na środek miasta/kraju (zbyt ogólne zapytania
geokodera) i poprawia znane błędne punkty. Bez pinezki wpis pokazuje się na mapie w swojej dzielnicy.
DRY=1 – tylko lista."""
import json, os, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import run as R
import geocode as G

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
dry = bool(os.environ.get("DRY"))
cache = json.load(open(G.CACHE))
bad = set()
for q, v in cache.items():
    head, city = q.rsplit(",", 1)[0], q.rsplit(",", 1)[-1].strip()
    if v and G.too_generic(head, city):
        bad.add((round(v[0], 5), round(v[1], 5)))
# znane błędy: Louvre dostał punkt Guggenheima
FIX = {"louvre abu dhabi": [24.5338, 54.3983]}
for k in list(cache):
    if k.lower().startswith("louvre abu dhabi") and "auditorium" not in k.lower():
        cache[k] = FIX["louvre abu dhabi"]
if not dry:
    json.dump(cache, open(G.CACHE, "w"), ensure_ascii=False)

n_clear = n_fix = 0
shared = defaultdict(set)
for table, col in (("events", "venue"), ("places", "name"), ("deals", "venue")):
    rows = db.get(table, {"select": f"id,{col},city,lat,lng", "lat": "not.is.null", "status": "neq.rejected", "limit": "20000"})
    for r in rows:
        name = (r.get(col) or "")
        pt = (round(r["lat"], 5), round(r["lng"], 5))
        shared[pt].add(name)
        if name.lower().startswith("louvre abu dhabi") and "auditorium" not in name.lower() and pt != tuple(FIX["louvre abu dhabi"]):
            n_fix += 1
            print(f"G|FIX {table}: {name} -> Louvre")
            if not dry:
                db.update(table, {"id": r["id"]}, {"lat": FIX["louvre abu dhabi"][0], "lng": FIX["louvre abu dhabi"][1]})
        elif pt in bad:
            n_clear += 1
            print(f"G|CLEAR {table}: {name[:70]} ({r['city']})")
            if not dry:
                db.update(table, {"id": r["id"]}, {"lat": None, "lng": None})
print(f"G|pinezki na środku miasta usunięte: {n_clear}, Louvre poprawiony: {n_fix}")
for pt, names in sorted(shared.items(), key=lambda x: -len(x[1]))[:8]:
    if len(names) >= 4:
        print(f"G|WSPÓLNY PUNKT {pt}: {len(names)} nazw, np. {sorted(names)[:4]}")
