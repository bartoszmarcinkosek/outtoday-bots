import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ALC = re.compile(r"alcohol|beer|wine|hops|grape|cocktail|spirits|bubbl|prosecco|champagne|sangria|pint|beverage package|house drinks|premium drinks|free.?flow|happy hour|ladies.?night|bar\b|pub\b", re.I)
rows = db.get("deals", {"select": "id,title,venue,deal_type,price_text,details,status", "city": "eq.Sharjah", "status": "in.(approved,pending)", "limit": "1000"})
print("SH", len(rows))
for d in rows:
    blob = " ".join(str(d.get(k) or "") for k in ("title", "venue", "deal_type", "price_text", "details"))
    print(("ALC|" if ALC.search(blob) else "OK|") + json.dumps({k: d.get(k) for k in ("id", "title", "venue", "deal_type", "price_text")}, ensure_ascii=False)[:260])
ev = db.get("events", {"select": "id,title,venue,category", "city": "eq.Sharjah", "status": "eq.approved", "limit": "2000"})
for e in ev:
    if ALC.search(e["title"] + " " + (e.get("venue") or "")): print("EV|" + json.dumps(e, ensure_ascii=False)[:200])
