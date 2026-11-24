"""Jednorazowo: stand-upy z "music"/"nightlife"/"culture" -> kategoria "comedy". DRY=1 tylko pokazuje."""
import os, re, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
RX = re.compile(r"comedy|stand[- ]?up|comedian|improv\b|laugh", re.I)
NOT = re.compile(r"comic con|based on the play|paddle|sup\b|stand[- ]?up paddl|musical comedy|comedy of errors|workshop|class\b|course|open mic night music", re.I)
today = dt.date.today().isoformat()
n = 0
for e in db.get("events", {"select": "id,title,category,description,start_date,end_date", "status": "in.(approved,pending)", "limit": "8000"}):
    if (e.get("end_date") or e["start_date"]) < today or e.get("category") == "comedy":
        continue
    t = e["title"] or ""
    d = (e.get("description") or "")[:200]
    hit = RX.search(t) or (e.get("category") in ("music", "nightlife") and re.search(r"stand[- ]?up comed|comedian|comedy (show|night|special|tour)", d, re.I))
    if not hit or NOT.search(t):
        continue
    n += 1
    print(f"FC|{e['category']}|{t[:70]}")
    if not os.environ.get("DRY"):
        db.update("events", {"id": e["id"]}, {"category": "comedy"})
print(f"FC|razem {n}")
