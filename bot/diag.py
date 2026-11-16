import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("events", {"select": "id,title,start_date,start_time,venue,city,price_text,source_name,url",
                         "status": "eq.pending", "source_name": "ilike.*meetup*", "order": "city,start_date", "limit": "500"})
print("PENDING MEETUP", len(rows))
for r in rows:
    print("ROW", r["id"], "|", r["city"], "|", r["start_date"], r.get("start_time"), "|", r["title"], "|", r.get("venue"), "|", r.get("price_text"), "|", r["source_name"], "|", r.get("url"))
uaq = db.get("events", {"select": "title,start_date,status", "city": "eq.Umm Al Quwain", "start_date": f"gte.{R.today_uae().isoformat()}"})
print("UAQ", uaq)
