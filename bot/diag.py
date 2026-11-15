import collections, os, requests, datetime
URL = os.environ["SUPABASE_URL"].strip(); KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
r = requests.get(f"{URL}/rest/v1/events", headers={"apikey": KEY}, params={"select": "source_name,status,start_date,end_date", "city": "ilike.*dubai*", "limit": "3000"}, timeout=30)
rows = r.json(); today = "2026-11-15"; wk = "2026-11-22"
c = collections.Counter((x["source_name"], x["status"]) for x in rows if (x["end_date"] or x["start_date"]) >= today)
for k, v in sorted(c.items()): print("SRC", k, v)
thisweek = [x for x in rows if x["status"]=="approved" and x["start_date"] <= wk and (x["end_date"] or x["start_date"]) >= today]
print("WEEK", len(thisweek), "TODAY", sum(1 for x in rows if x["status"]=="approved" and x["start_date"]<=today<=(x["end_date"] or x["start_date"])))
