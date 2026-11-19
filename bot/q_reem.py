import os, datetime as dt, re
import run as R
db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
today = dt.date.today().isoformat()
pat = re.compile(r"reem|okhtama|shams|gate tower|sky tower|boutik|marina square|tamouh", re.I)
for t, cols, extra in (("events", "title,venue,area,start_date,end_date,status", {"or": f"(end_date.gte.{today},start_date.gte.{today})"}),
                       ("places", "name,area,status", {}), ("deals", "title,venue,area,status", {})):
    rows = db.get(t, {"select": cols, "limit": "10000", **extra})
    hit = [r for r in rows if pat.search(" ".join(str(v) for v in r.values() if v))]
    print("ROW", t, "razem", len(rows), "Reem", len(hit), "approved", sum(r["status"] == "approved" for r in hit))
    for r in hit[:25]:
        print("ROW   ", r)
