import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for e in db.get("events", {"select": "id,title,url,official_url,source_url", "official_url": "like.*/tags/*", "limit": "200"}):
    print("BL|" + json.dumps(e, ensure_ascii=False))
