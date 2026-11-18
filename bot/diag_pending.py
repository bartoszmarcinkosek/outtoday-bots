import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,price_text,official_url,source_name,description", "status": "eq.pending", "order": "start_date.asc", "limit": "200"})
for e in ev: print("P|" + json.dumps(e, ensure_ascii=False)[:700])
ch = db.get("bot_changes", {"select": "*", "handled": "eq.false", "limit": "200"})
for c in ch: print("C|" + json.dumps(c, ensure_ascii=False)[:700])
