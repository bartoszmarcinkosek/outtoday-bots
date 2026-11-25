"""Tylko odczyt: nocna paczka kontroli jakości WEDŁUG RYZYKA (zamiast po kolei).
Kiedy pozycja była ostatnio obejrzana: audit/reviewed.json {id: "RRRR-MM-DD"} (brak wpisu = 2026-11-24, dzień pełnego przeglądu).
Co ile dni pozycja ma być oglądana: wydarzenia w najbliższych 7 dniach – 4, pozostałe wydarzenia – 14, oferty – 14, miejsca – 30.
Bierze 100 najbardziej zaległych (SIZE), wypisuje je pogrupowane: miejsca, oferty, wydarzenia (wg miasta i daty)."""
import os, sys, json, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
A = os.path.join(os.path.dirname(__file__), "..", "audit")
try:
    seen = json.load(open(os.path.join(A, "reviewed.json")))
except Exception:
    seen = {}
size = int(os.environ.get("SIZE", "100"))
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date()
ts, wk = today.isoformat(), (today + dt.timedelta(days=7)).isoformat()
def age(i):
    try:
        return (today - dt.date.fromisoformat(seen.get(i, "2026-11-24"))).days
    except Exception:
        return 99
def cell(x, k=150):
    return str(x if x is not None else "").replace("|", "/").replace("\n", " ")[:k]
cand = []   # (zaległość, kolejność grupy, klucz sortowania, linia)
for r in db.get("places", {"select": "id,name,category,area,city,hours_text,price_text,is_free,official_url,description", "status": "eq.approved", "limit": "3000"}):
    cand.append((age(r["id"]) / 30, 0, (r["city"] or "", r["category"] or "", r["name"] or ""),
                 "AP|" + "|".join(cell(r.get(k)) for k in ("id", "city", "category", "name", "area", "hours_text", "price_text", "is_free", "official_url", "description"))))
for r in db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,start_time,end_time,price_text,valid_until,official_url,details", "status": "eq.approved", "limit": "3000"}):
    cand.append((age(r["id"]) / 14, 1, (r["city"] or "", r["venue"] or "", r["deal_type"] or ""),
                 "AL|" + "|".join(cell(r.get(k)) for k in ("id", "city", "venue", "deal_type", "title", "days_of_week", "start_time", "end_time", "price_text", "valid_until", "official_url", "details"))))
soon = 0
for r in db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,category,price_text,is_free,official_url,source_name,description", "status": "eq.approved", "limit": "5000"}):
    if (r.get("end_date") or r["start_date"]) < ts:
        continue
    near = r["start_date"] <= wk
    soon += near
    cand.append((age(r["id"]) / (4 if near else 14), 2, (r["city"] or "", r["start_date"], r["title"] or ""),
                 "AE|" + "|".join(cell(r.get(k)) for k in ("id", "city", "start_date", "end_date", "start_time", "category", "title", "venue", "price_text", "is_free", "official_url", "source_name", "description"))))
due = [c for c in cand if c[0] >= 1]
pick = sorted(cand, key=lambda c: -c[0])[:size]
print(f"AB|risk batch | {len(pick)} of {len(cand)} items | overdue now {len(due)} | events in next 7 days {soon}")
for c in sorted(pick, key=lambda c: (c[1], c[2])):
    print(c[3])
