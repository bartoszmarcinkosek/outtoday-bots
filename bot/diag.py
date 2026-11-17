import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("places", {"select": "id,name,city,category,status", "status": "eq.approved", "order": "city,name", "limit": "2000"})
for r in rows:
    print("PL", r["id"], "|", r["city"], "|", r["category"], "|", r["name"])
