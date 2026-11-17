import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("events", {"select": "title,start_date,end_date,start_time,venue,city,status", "start_date": "lte.2026-12-04",
                         "or": "(end_date.gte.2026-11-29,start_date.gte.2026-11-29)", "status": "neq.rejected", "order": "start_date", "limit": "500"})
for r in rows:
    if r["start_date"] >= "2026-11-29" or "etihad" in r["title"].lower() or "national day" in r["title"].lower():
        print("EV", r["status"], "|", r["start_date"], r.get("start_time"), "|", r["city"], "|", r["title"], "|", r.get("venue"))
