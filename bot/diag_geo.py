"""Tylko odczyt: współrzędne w Al Ain – ile wpisów ma te same (np. środek miasta)."""
import os, sys, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for t, name in (("events", "title"), ("places", "name"), ("deals", "title")):
    rows = db.get(t, {"select": f"id,{name},venue,lat,lng" if t != "places" else f"id,{name},lat,lng",
                      "city": "eq.Al Ain", "status": "eq.approved", "limit": "2000"})
    c = collections.Counter((round(r["lat"], 4), round(r["lng"], 4)) for r in rows if r.get("lat") is not None)
    nogeo = sum(1 for r in rows if r.get("lat") is None)
    print(f"G|{t}|razem {len(rows)}|bez wsp. {nogeo}|unikalnych punktów {len(c)}|najczęstsze {c.most_common(4)}")
    top = c.most_common(1)
    if top and top[0][1] > 2:
        for r in rows:
            if r.get("lat") is not None and (round(r["lat"], 4), round(r["lng"], 4)) == top[0][0]:
                print(f"G|  {r[name][:50]} @{(r.get('venue') or '')[:30]}")
for t, name in (("events", "title"), ("places", "name"), ("deals", "title")):
    sel = f"id,{name},venue,lat" if t != "places" else f"id,{name},address,lat"
    for r in db.get(t, {"select": sel, "city": "eq.Al Ain", "status": "eq.approved", "lat": "is.null", "limit": "200"}):
        print(f"GN|{t}|{r[name][:50]}|{(r.get('venue') or r.get('address') or '')[:70]}|{r['id']}")
