import os, sys, json, re
from urllib.parse import urlparse
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ti = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,official_url,url,source_name", "status": "eq.approved",
                       "or": f"(end_date.gte.{ti},and(end_date.is.null,start_date.gte.{ti}))", "limit": "8000"})
bad = []
for e in ev:
    u = e.get("official_url") or ""
    p = urlparse(u)
    generic = (not u) or p.path in ("", "/") or re.search(r"/(event/list|shows|festival|events?|whats-on)/?$", p.path or "")
    if generic and not (e.get("url") and urlparse(e["url"]).path not in ("", "/")):
        bad.append(e)
bad.sort(key=lambda e: e["start_date"])
print(f"L|total {len(ev)} bad {len(bad)}")
for e in bad: print("L|" + json.dumps({k: e.get(k) for k in ("id","title","venue","city","start_date","end_date","official_url","source_name")}, ensure_ascii=False)[:330])
