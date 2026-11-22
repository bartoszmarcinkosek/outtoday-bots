"""Tylko odczyt: jakie wpisy dostają jakie zdjęcie (logika jak app/src/photos.ts) – do przeglądu dopasowań."""
import os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import run as R
src = open(os.path.join(os.path.dirname(__file__), "..", "app", "src", "photos.ts")).read()
def pairs(block):
    return [(re.compile(m.group(1), re.I), m.group(2)) for m in re.finditer(r"\[/(.+?)/i, '([a-z_0-9]+)'\]", block)]
LM = pairs(src[src.index("const LANDMARKS"):src.index("const VENUES")])
RU = pairs(src[src.index("const RULES"):src.index("const CAT")])
CAT = dict(re.findall(r"(\w+): \['(\w+)'\]", src[src.index("const CAT"):src.index("const CITY_SUFFIX")]))
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
import datetime as dt
today = dt.date.today().isoformat()
rows = [("event", r["title"], r.get("venue") or "", r.get("category")) for r in db.get("events", {"select": "title,venue,category,start_date,end_date", "status": "eq.approved", "limit": "9000"}) if (r.get("end_date") or r["start_date"]) >= today]
rows += [("place", r["name"], "", r.get("category")) for r in db.get("places", {"select": "name,category", "status": "eq.approved", "limit": "9000"})]
rows += [("deal", r["title"], r.get("venue") or "", r.get("deal_type")) for r in db.get("deals", {"select": "title,venue,deal_type", "status": "eq.approved", "limit": "9000"})]
g = defaultdict(list)
for kind, title, place, cat in rows:
    key = None
    lm = next((k for re_, k in LM if re_.search(f"{title} {place}")), None)
    if lm in ("lm_palm", "lm_saadiyat", "lm_corniche", "lm_reem") and kind != "place":
        lm = None
    if lm:
        lre = next(re_ for re_, k in LM if k == lm)
        rest = lre.sub(" ", title)
        hit = next((k for re_, k in RU if re_.search(rest)), None) if kind != "deal" else None
        key = hit or lm
    else:
        if kind != "deal" or not cat or cat == "other":
            key = next((k for re_, k in RU if re_.search(title)), None)
        if not key and kind == "event":
            key = "(IKONKA)"
        key = key or CAT.get(cat, f"(brak:{cat})")
    g[key].append(f"{kind[0]}:{cat}:{title[:55]}")
for k in sorted(g):
    v = g[k]
    print(f"A|{k} ({len(v)})|" + " ; ".join(v[:25]))
