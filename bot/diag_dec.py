"""Tylko odczyt: grudniowe eventy bez dobrego linku (jak fill_links only=december) + 2 złe tytuły."""
import os, re, sys, json
from urllib.parse import urlparse
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,price_text,is_free,official_url,url,source_name,description",
                       "status": "eq.approved", "and": "(start_date.gte.2026-12-01,start_date.lte.2026-12-31)", "limit": "5000"})
def generic(u):
    p = urlparse(u or "")
    return (not u) or p.path in ("", "/") or bool(re.search(r"/(event/list|shows|festival|events?|whats-on)/?$", p.path or ""))
bad = [e for e in ev if generic(e.get("official_url")) and generic(e.get("url")) and "platinumlist" not in (e.get("source_name") or "").lower()]
need = lambda e: (not e.get("start_time")) or (not e.get("price_text") and not e.get("is_free"))
print(f"D|bez dobrego linku: {len(bad)}, z nich z brakami: {len([e for e in bad if need(e)])}")
for e in sorted(bad, key=lambda e: e["start_date"]):
    print("D|L|" + json.dumps({k: e.get(k) for k in ("start_date", "title", "venue", "city", "source_name", "official_url", "url")}, ensure_ascii=False))
for e in ev:
    if re.search(r"Show on 27th|Drone Show at Bluewaters", e["title"]):
        print("D|T|" + json.dumps(e, ensure_ascii=False))
