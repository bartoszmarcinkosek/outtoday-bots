import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for r in db.get("places", {"select": "*", "name": "ilike.*grand mosque*"}):
    print("L|" + json.dumps({k: r.get(k) for k in ("id","name","city","status","is_free","price_text","hours_text","official_url","description")}, ensure_ascii=False))
for r in db.get("places", {"select": "id,name,city,is_free,price_text,official_url", "status": "eq.approved", "is_free": "eq.true", "limit": "500"}):
    print("L|FREE " + json.dumps(r, ensure_ascii=False)[:200])
