"""Czy te same rzeczy są w dwóch zakładkach (events / places / deals)?"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,category", "status": "eq.approved",
                       "or": f"(end_date.gte.{today},and(end_date.is.null,start_date.gte.{today}))", "limit": "6000"})
pl = db.get("places", {"select": "id,name,city,category", "status": "eq.approved", "limit": "3000"})
dl = db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week", "status": "eq.approved", "limit": "3000"})
n = 0
for e in ev:
    for d in dl:
        if e["city"] == d["city"] and R.titles_match(e["title"], d["title"]) and e.get("venue") and d.get("venue") and \
                (set(R._tokens(e["venue"])) & set(R._tokens(d["venue"]))):
            n += 1; print("ED|", e["title"], "|", e["venue"], "||", d["title"], "|", d["venue"])
for e in ev:
    long = e.get("end_date") and e["end_date"] > e["start_date"]
    for p in pl:
        if e["city"] == p["city"] and R.titles_match(e["title"], p["name"]):
            n += 1; print("EP|", e["title"], e["start_date"], e.get("end_date"), "||", p["name"], p["category"])
for d in dl:
    for p in pl:
        if d["city"] == p["city"] and R.titles_match(d["title"], p["name"]):
            n += 1; print("DP|", d["title"], d["deal_type"], "||", p["name"], p["category"], "|ID", p["id"])
print("CROSS", n)
