import json, os, sys, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
pl = db.get("places", {"select": "id,name,hours_text,category", "status": "eq.approved", "limit": "5000"})
print("PLACES", len(pl), "with hours", sum(1 for p in pl if p.get("hours_text")))
c = collections.Counter(p.get("hours_text") for p in pl if p.get("hours_text"))
for h, n in c.most_common(400):
    print("H|", n, "|", h)
