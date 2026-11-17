import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
q = os.environ.get("Q", "yasmarinacircuit")
for t, cols in (("places", "id,name,status,hours_text,official_url,url,source_url"), ("events", "id,title,status,start_date,official_url"), ("deals", "id,title,status,official_url")):
    try:
        rows = db.get(t, {"select": cols, "or": f"(official_url.ilike.*{q}*,{'name' if t=='places' else 'title'}.ilike.*train*)", "limit": "50"})
    except Exception as e:
        rows = [str(e)[:200]]
    for r in rows: print("F|", t, json.dumps(r, ensure_ascii=False)[:400])
