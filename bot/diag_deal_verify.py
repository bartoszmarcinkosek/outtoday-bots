"""Tylko odczyt: N ofert (domyślnie 14) do porównania ze stroną źródłową – te najdawniej sprawdzone
(audit/deal_verified.json {id: data}; brak wpisu = nigdy). Tylko oferty z linkiem."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
try:
    seen = json.load(open(os.path.join(os.path.dirname(__file__), "..", "audit", "deal_verified.json")))
except Exception:
    seen = {}
n = int(os.environ.get("N", "14"))
def cell(x, k=220):
    return str(x if x is not None else "").replace("|", "/").replace("\n", " ")[:k]
rows = [r for r in db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,start_time,end_time,price_text,valid_until,official_url,details,created_at",
                                    "status": "eq.approved", "limit": "3000"}) if (r.get("official_url") or "").startswith("http")]
rows.sort(key=lambda r: (seen.get(r["id"], "0"), r.get("created_at") or ""))
never = sum(1 for r in rows if r["id"] not in seen)
print(f"DA|deals with link {len(rows)} | never verified {never}")
for r in rows[:n]:
    print("DV|" + "|".join(cell(r.get(k)) for k in ("id", "city", "venue", "deal_type", "title", "days_of_week", "start_time", "end_time", "price_text", "valid_until", "official_url", "details")))
