"""Tylko odczyt: szerokie szukanie duplikatów, których nocna kontrola nie łapie.
D1 eventy: to samo miasto, podobny tytuł, nakładające się daty (także inny dzień startu / inne miejsce).
D2 oferty: to samo miejsce (venue), podobny tytuł, ten sam typ.
D3 miejsca: podobna nazwa w tym samym mieście."""
import os, sys, re, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = dt.date.today().isoformat()
ev = [e for e in db.get("events", {"select": "id,title,start_date,end_date,start_time,city,venue", "status": "eq.approved", "limit": "8000"})
      if (e.get("end_date") or e["start_date"]) >= today]
def clean(t):
    t = re.sub(r"\((?:[^)]*\d[^)]*)\)", " ", t or "")
    t = re.sub(r"\b20\d\d\b|\blive\b|\b(?:in|at)\s+(?:abu dhabi|dubai|sharjah|al ain|ras al khaimah|ajman|fujairah)\b", " ", t, flags=re.I)
    return re.sub(r"\s+", " ", t).strip()
def ct(e, f="title"):
    t = e[f] or ""
    v = (e.get("venue") or "").split(",")[0].strip()
    if v and len(v) > 3:
        t = re.sub(r"\b(?:at|@)\s+" + re.escape(v), " ", t, flags=re.I)
    return clean(t)
def span(e):
    return e["start_date"], (e.get("end_date") or e["start_date"])
by_city = {}
for e in ev: by_city.setdefault(e["city"], []).append(e)
n = 0
for city, rows in by_city.items():
    rows.sort(key=lambda e: e["start_date"])
    for i, a in enumerate(rows):
        for b in rows[i+1:i+400]:
            if a["start_time"] and b["start_time"] and a["start_time"] != b["start_time"] and a["start_date"] == b["start_date"]:
                continue
            ta, tb = ct(a), ct(b)
            if len(R._tokens(ta)) < 2 and len(R._tokens(tb)) < 2 and R.norm(ta) != R.norm(tb):
                continue
            if not R.titles_match(ta, tb):
                continue
            sa, sb = span(a), span(b)
            overlap = sa[0] <= sb[1] and sb[0] <= sa[1]
            near = abs((dt.date.fromisoformat(a["start_date"]) - dt.date.fromisoformat(b["start_date"])).days) <= 14
            if overlap or near:
                n += 1
                print(f"D1|{city}|{sa[0]}..{sa[1]} {a.get('start_time') or ''} {a['title'][:50]} @{(a.get('venue') or '')[:25]} #{a['id']}"
                      f" <> {sb[0]}..{sb[1]} {b.get('start_time') or ''} {b['title'][:50]} @{(b.get('venue') or '')[:25]} #{b['id']}")
dl = db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,start_time", "status": "eq.approved", "limit": "5000"})
by_v = {}
for d in dl: by_v.setdefault((d["city"], R.norm((d.get("venue") or "").split(",")[0])), []).append(d)
for k, rows in by_v.items():
    for i, a in enumerate(rows):
        for b in rows[i+1:]:
            if a["deal_type"] == b["deal_type"] and (R.titles_match(a["title"], b["title"]) or R.norm(a["title"]) == R.norm(b["title"])):
                n += 1
                print(f"D2|{k[0]}|{a['deal_type']}|{a['title'][:50]} [{a.get('days_of_week')}] #{a['id']} <> {b['title'][:50]} [{b.get('days_of_week')}] #{b['id']} @{(a.get('venue') or '')[:30]}")
pl = db.get("places", {"select": "id,name,city", "status": "eq.approved", "limit": "5000"})
by_c = {}
for p in pl: by_c.setdefault(p["city"], []).append(p)
for c, rows in by_c.items():
    for i, a in enumerate(rows):
        for b in rows[i+1:]:
            if R.titles_match(a["name"], b["name"]):
                n += 1
                print(f"D3|{c}|{a['name']} #{a['id']} <> {b['name']} #{b['id']}")
print(f"D9|kandydatów {n} (eventy {len(ev)}, oferty {len(dl)}, miejsca {len(pl)})")
