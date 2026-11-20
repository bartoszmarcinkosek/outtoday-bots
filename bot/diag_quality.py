"""Tylko odczyt: przegląd jakości – duplikaty (ten sam tytuł + data + miasto) i tytuły ALL CAPS
w eventach, ofertach i miejscach (pending + approved). Nic nie zmienia."""
import os, re, sys, json
from collections import defaultdict
sys.path.insert(0, os.path.dirname(__file__))
import run as R

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
WATCH = ["7s", "jam jar", "desert safari", "atif aslam", "twerk", "iifa", "kino"]


def caps(t):
    w = [x for x in re.findall(r"[A-Za-z]{3,}", t or "")]
    return len(w) >= 2 and sum(x.isupper() for x in w) / len(w) >= 0.6


def out(tag, r):
    print(f"Q|{tag}|" + json.dumps(r, ensure_ascii=False)[:500])


ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,price_text,status,source_name,official_url,url,description",
                       "status": "in.(pending,approved)", "start_date": "gte.2026-11-20", "limit": "8000"})
de = db.get("deals", {"select": "id,title,venue,city,status,deal_type,days_of_week,price_text,official_url",
                      "status": "in.(pending,approved)", "limit": "8000"})
pl = db.get("places", {"select": "id,name,city,area,status,official_url", "status": "in.(pending,approved)", "limit": "8000"})
print(f"Q|count|events {len(ev)} deals {len(de)} places {len(pl)}")

g = defaultdict(list)
for e in ev:
    g[(R.norm(e["title"]), e["start_date"], (e.get("city") or "").lower())].append(e)
for k, v in g.items():
    if len(v) > 1:
        print("Q|DUP-EV ----")
        for e in v:
            out("DUP-EV", {x: e.get(x) for x in ("id", "title", "venue", "start_date", "start_time", "price_text", "status", "source_name", "official_url")} | {"desc": bool(e.get("description"))})
g = defaultdict(list)
for d in de:
    g[(R.norm(d["title"]), R.norm(d.get("venue")))].append(d)
for k, v in g.items():
    if len(v) > 1:
        print("Q|DUP-DEAL ----")
        for d in v:
            out("DUP-DEAL", d)
g = defaultdict(list)
for p in pl:
    g[(R.norm(p["name"]), (p.get("city") or "").lower())].append(p)
for k, v in g.items():
    if len(v) > 1:
        print("Q|DUP-PL ----")
        for p in v:
            out("DUP-PL", p)

for e in ev:
    if caps(e["title"]):
        out("CAPS-EV", {"id": e["id"], "title": e["title"], "start_date": e["start_date"], "status": e["status"]})
for d in de:
    if caps(d["title"]):
        out("CAPS-DEAL", {"id": d["id"], "title": d["title"], "venue": d.get("venue")})
for p in pl:
    if caps(p["name"]):
        out("CAPS-PL", {"id": p["id"], "name": p["name"]})

for row, tab in [(e, "ev") for e in ev] + [(d, "deal") for d in de]:
    t = (row.get("title") or "").lower() + " " + (row.get("venue") or "").lower()
    if any(w in t for w in WATCH):
        out("WATCH-" + tab, {k: row.get(k) for k in ("id", "title", "venue", "start_date", "status", "source_name", "deal_type")})
