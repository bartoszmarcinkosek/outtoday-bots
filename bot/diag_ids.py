import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "id,title,start_date,end_date,venue,city,status", "status": "eq.approved", "start_date": "gte.2026-11-15", "limit": "8000"})
for e in ev:
    if re.search(r"RAK Night Market|Al Marjan Island|Eid Al Etihad|Kalba|Wadi Al Helo|Masfout|RAK EATS|Your Fort|Al Rams|Kshisha|Khawaneej|Eid al Etihad", e["title"], re.I):
        print("D|" + json.dumps(e, ensure_ascii=False))
