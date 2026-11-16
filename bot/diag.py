import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("deals", {"select": "id,title,venue,official_url,status", "source_name": "eq.OutToday hotel bot (official site)"})
for r in rows:
    bad = re.search(r"seychelles|festive|spa", (r["official_url"] or "") + " " + r["title"], re.I)
    if bad:
        db.update("deals", {"id": r["id"]}, {"status": "rejected"})
    print("ROW", "REJ" if bad else "OK ", r["title"], "|", r["venue"], "|", r["official_url"])
