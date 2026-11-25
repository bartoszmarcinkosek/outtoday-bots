"""Tylko odczyt: pełne dane pozycji o id z audit/show_ids.txt (po jednym w linii)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ids = [l.split()[0] for l in open(os.path.join(os.path.dirname(__file__), "..", "audit", "show_ids.txt")) if l.strip()]
for t in ("events", "deals", "places"):
    for i in range(0, len(ids), 40):
        for r in db.get(t, {"select": "*", "id": "in.(" + ",".join(ids[i:i + 40]) + ")"}):
            keep = {k: v for k, v in r.items() if v not in (None, "", []) and k in ("id", "title", "name", "venue", "area", "city", "status", "start_date", "end_date", "start_time", "end_time", "days_of_week", "deal_type", "price_text", "is_free", "official_url", "details", "description", "valid_until", "source_name", "lat", "lng")}
            print(f"SH|{t}|" + json.dumps(keep, ensure_ascii=False)[:1100])
