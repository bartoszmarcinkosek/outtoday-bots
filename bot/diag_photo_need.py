"""Tylko odczyt: ile wpisów trafia do każdej puli zdjęć (te same reguły co app/src/photos.ts) -> ile zdjęć potrzeba."""
import os, re, sys, json, math, datetime as dt
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
import run as R
src = open(os.path.join(os.path.dirname(__file__), "..", "app", "src", "photos.ts")).read()
def pairs(block):
    return [(re.compile(m.group(1), re.I), m.group(2)) for m in re.finditer(r"\[/(.+?)/i, '([a-z_0-9]+)'\]", block)]
LM = pairs(src[src.index("const LANDMARKS"):src.index("const VENUES")])
RU = pairs(src[src.index("const RULES"):src.index("const CAT")])
CAT = dict(re.findall(r"(\w+): \['(\w+)'\]", src[src.index("const CAT"):src.index("const CITY_SUFFIX")]))
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = dt.date.today().isoformat()
ev = [r for r in db.get("events", {"select": "title,venue,category,start_date,end_date", "status": "eq.approved", "limit": "9000"}) if (r.get("end_date") or r["start_date"]) >= today]
pl = db.get("places", {"select": "name,category", "status": "eq.approved", "limit": "9000"})
de = db.get("deals", {"select": "title,venue,deal_type", "status": "eq.approved", "limit": "9000"})
c = Counter()
def key(kind, title, place, cat):
    t = f"{title} {place or ''}"
    for re_, k in LM:
        if re_.search(t): return k
    if kind != "deal" or not cat or cat == "other":
        for re_, k in RU:
            if re_.search(title): return k
    return CAT.get(cat, f"(brak:{cat})")
for e in ev: c[key("event", e["title"], e.get("venue"), e.get("category"))] += 1
for p in pl: c[key("place", p["name"], "", p.get("category"))] += 1
for d in de: c[key("deal", d["title"], d.get("venue"), d.get("deal_type"))] += 1
print(f"N|eventy {len(ev)}, miejsca {len(pl)}, oferty {len(de)}, razem {len(ev)+len(pl)+len(de)}, pul {len(c)}")
for k, n in c.most_common():
    print(f"N|{k}|{n}")
