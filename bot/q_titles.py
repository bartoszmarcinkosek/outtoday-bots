import os, re, collections, run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "title,category,start_date", "status": "eq.approved", "start_date": "gte.2026-11-19", "limit": "8000"})
hits = [e for e in ev if re.search(r"market|bazaar|souq|souk|flea|car boot|farmers", e["title"], re.I)]
print("M |", len(hits), collections.Counter(e["category"] for e in hits))
for e in hits[:40]: print("M |", e["start_date"], e["category"], e["title"][:70])
