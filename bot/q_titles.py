import os, re, run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "id,title,category", "status": "eq.approved", "start_date": "gte.2026-11-19", "limit": "8000"})
for e in ev:
    if re.search(r"market|bazaar|souq|souk|flea|car boot|farmers", e["title"], re.I): print("M |", e["id"], "|", e["category"], "|", e["title"][:70])
