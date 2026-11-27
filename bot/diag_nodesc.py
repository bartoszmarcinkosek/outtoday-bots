"""Tylko odczyt: nadchodzące wydarzenia, oferty i miejsca bez opisu (ND|kind|id|city|title|venue|url)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
t = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,city,title,venue,description,official_url,start_date", "status": "eq.approved", "or": f"(end_date.gte.{t},and(end_date.is.null,start_date.gte.{t}))", "limit": "3000"})
dl = db.get("deals", {"select": "id,city,title,venue,details,official_url", "status": "eq.approved", "limit": "3000"})
pl = db.get("places", {"select": "id,city,name,description,official_url", "status": "eq.approved", "limit": "3000"})
short = lambda s: len((s or "").strip()) < 40  # noqa: E731
a = [e for e in ev if short(e.get("description"))]
b = [d for d in dl if short(d.get("details"))]
c = [p for p in pl if short(p.get("description"))]
print(f"NZ|events {len(a)}/{len(ev)}|deals {len(b)}/{len(dl)}|places {len(c)}/{len(pl)}")
for e in sorted(a, key=lambda e: e["start_date"]):
    print(f"ND|event|{e['id']}|{e['city']}|{e['start_date']}|{e['title']}|{e.get('venue') or ''}|{e.get('official_url') or ''}")
for d in b:
    print(f"ND|deal|{d['id']}|{d['city']}||{d['title']}|{d.get('venue') or ''}|{d.get('official_url') or ''}")
for p in c:
    print(f"ND|place|{p['id']}|{p['city']}||{p['name']}||{p.get('official_url') or ''}")
