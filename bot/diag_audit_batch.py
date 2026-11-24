"""Tylko odczyt: jedna paczka pełnego przeglądu (audit/state.json -> next, size).
Kolejność stała: miejsca, oferty, wydarzenia (nadchodzące); w każdej tabeli wg miasta; wydarzenia wg daty, żeby duplikaty były obok siebie.
Bierze tylko pozycje dodane przed 'cutoff' (nowsze sprawdza codzienny przegląd)."""
import os, sys, json, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
st = json.load(open(os.path.join(os.path.dirname(__file__), "..", "audit", "state.json")))
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
PAR = os.environ.get("PARITY", "")
ROLL = os.environ.get("ROLL") == "1"   # ciągły przegląd: bez daty granicznej, licznik audit/roll_next.txt, po końcu od zera
cut, size = ("2999-01-01" if ROLL else st["cutoff"]), st["size"]
_f = os.path.join(os.path.dirname(__file__), "..", "audit", "roll_next.txt" if ROLL else f"next_{PAR}.txt")
n = int(os.environ.get("BATCH") or open(_f).read().strip())
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date().isoformat()
def cell(x, k=150):
    return str(x if x is not None else "").replace("|", "/").replace("\n", " ")[:k]
items = []
for r in sorted(db.get("places", {"select": "id,name,category,area,city,hours_text,price_text,is_free,official_url,description", "status": "eq.approved",
                                  "created_at": f"lt.{cut}", "limit": "3000"}), key=lambda r: (r["city"] or "", r["category"] or "", r["name"] or "")):
    items.append("AP|" + "|".join(cell(r.get(k)) for k in ("id", "city", "category", "name", "area", "hours_text", "price_text", "is_free", "official_url", "description")))
for r in sorted(db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,start_time,end_time,price_text,valid_until,official_url,details",
                                 "status": "eq.approved", "created_at": f"lt.{cut}", "limit": "3000"}), key=lambda r: (r["city"] or "", r["venue"] or "", r["deal_type"] or "")):
    items.append("AL|" + "|".join(cell(r.get(k)) for k in ("id", "city", "venue", "deal_type", "title", "days_of_week", "start_time", "end_time", "price_text", "valid_until", "official_url", "details")))
ev = db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,category,price_text,is_free,official_url,source_name,description",
                       "status": "eq.approved", "created_at": f"lt.{cut}", "limit": "5000"})
ev = [r for r in ev if (r.get("end_date") or r["start_date"]) >= today]
for r in sorted(ev, key=lambda r: (r["city"] or "", r["start_date"], r["title"] or "")):
    items.append("AE|" + "|".join(cell(r.get(k)) for k in ("id", "city", "start_date", "end_date", "start_time", "category", "title", "venue", "price_text", "is_free", "official_url", "source_name", "description")))
batches = (len(items) + size - 1) // size
if ROLL and n >= batches:
    n = 0
print(f"AB|batch {n} of {batches} (0-based) | total {len(items)} | size {size}")
for line in items[n * size:(n + 1) * size]:
    print(line)
