"""Tylko odczyt: wszystkie zatwierdzone oferty w mieście CITY (domyślnie Sharjah)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for r in sorted(db.get("deals", {"select": "id,title,venue,deal_type,days_of_week,start_time,end_time,price_text,details,official_url,created_at", "status": "eq.approved", "city": f"eq.{os.environ.get('CITY', 'Sharjah')}", "limit": "500"}), key=lambda r: (r.get("venue") or r["title"])):
    print("CD|" + "|".join(str(r.get(k) or "").replace("|", "/")[:110] for k in ("id", "deal_type", "title", "venue", "days_of_week", "start_time", "end_time", "price_text", "details", "official_url", "created_at")))
