"""Tylko odczyt: N ofert (domyślnie 40) do porównania ze stroną źródłową – te najdawniej sprawdzone
(audit/deal_verified.json {id: data}; brak wpisu = nigdy). Tylko oferty z linkiem."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
try:
    seen = json.load(open(os.path.join(os.path.dirname(__file__), "..", "audit", "deal_verified.json")))
except Exception:
    seen = {}
n = int(os.environ.get("N", "40"))
def cell(x, k=220):
    return str(x if x is not None else "").replace("|", "/").replace("\n", " ")[:k]
rows = [r for r in db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,start_time,end_time,price_text,valid_until,official_url,details,created_at",
                                    "status": "eq.approved", "limit": "3000"}) if (r.get("official_url") or "").startswith("http")]
# audit/deal_priority.txt: id-ki ofert, których strona zniknęła w kontroli linków – idą pierwsze (dopóki nie zostaną sprawdzone)
try:
    prio = {l.split()[0] for l in open(os.path.join(os.path.dirname(__file__), "..", "audit", "deal_priority.txt")) if l.strip() and not l.startswith("#")}
except Exception:
    prio = set()
prio = {i for i in prio if i not in seen}
rows.sort(key=lambda r: (r["id"] not in prio, seen.get(r["id"], "0"), r.get("created_at") or ""))
never = sum(1 for r in rows if r["id"] not in seen)
print("DN|days_of_week numbering in the database: 0 = Sunday, 1 = Monday, 2 = Tuesday, 3 = Wednesday, 4 = Thursday, 5 = Friday, 6 = Saturday")
print(f"DA|deals with link {len(rows)} | never verified {never}")
if prio:
    print(f"DN|the first {min(n, len(prio))} deals below had a dead or wrong link in the weekly link check (page 404 or another offer)")
for r in rows[:n]:
    print("DV|" + "|".join(cell(r.get(k)) for k in ("id", "city", "venue", "deal_type", "title", "days_of_week", "start_time", "end_time", "price_text", "valid_until", "official_url", "details")))
