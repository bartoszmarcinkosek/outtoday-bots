import os, sys, json, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ti = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,category,official_url,url,price_text,description", "status": "eq.approved", "end_date": f"gte.{ti}", "limit": "8000"})
L = [e for e in ev if (dt.date.fromisoformat(e["end_date"]) - dt.date.fromisoformat(e["start_date"])).days > 21]
L.sort(key=lambda e: e["category"] or "")
for e in L: print("L|" + json.dumps({k: (e.get(k) or "")[:120] if k=="description" else e.get(k) for k in ("id","title","category","venue","city","start_date","end_date","start_time","official_url","url","description")}, ensure_ascii=False))
print("L|N", len(L))
