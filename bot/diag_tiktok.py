"""Tylko odczyt: materiał na pierwszy tydzień TikToka."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for d in db.get("deals", {"select": "title,venue,city,price_text,days_of_week", "status": "eq.approved", "deal_type": "eq.brunch", "city": "eq.Abu Dhabi", "limit": "200"}):
    print(f"BR|{d['title'][:45]}|{(d.get('venue') or '')[:40]}|{(d.get('price_text') or '')[:60]}|{d.get('days_of_week')}")
for e in db.get("events", {"select": "title,venue,city,start_date,end_date,start_time,price_text", "status": "eq.approved", "is_free": "eq.true",
                           "start_date": "lte.2026-12-03", "or": "(end_date.gte.2026-12-01,start_date.gte.2026-12-01)", "limit": "200"}):
    if e["city"] in ("Abu Dhabi", "Dubai"):
        print(f"FR|{e['city']}|{e['start_date']}..{e.get('end_date') or ''}|{e['title'][:55]}|{(e.get('venue') or '')[:35]}")
for e in db.get("events", {"select": "title,venue,start_date,end_date,start_time,price_text,category", "status": "eq.approved", "city": "eq.Abu Dhabi",
                           "start_date": "lte.2026-12-06", "or": "(end_date.gte.2026-12-04,start_date.gte.2026-12-04)", "limit": "200"}):
    print(f"WE|{e['start_date']}..{e.get('end_date') or ''} {e.get('start_time') or ''}|{e['title'][:55]}|{(e.get('venue') or '')[:30]}|{(e.get('price_text') or '')[:30]}|{e.get('category')}")
for k in ["polish", "polonia", "polska", "poland"]:
    for e in db.get("events", {"select": "title,venue,city,start_date", "status": "eq.approved", "title": f"ilike.*{k}*", "start_date": "gte.2026-11-28", "limit": "20"}):
        print(f"PL|{e['start_date']}|{e['title'][:60]}|{e.get('venue')}|{e['city']}")
