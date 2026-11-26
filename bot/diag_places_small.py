"""Tylko odczyt: miejsca w mniejszych emiratach (PL|city|category|status|name|url)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for p in sorted(db.get("places", {"select": "city,category,status,name,official_url", "city": "in.(Ajman,Umm Al Quwain,Fujairah,Ras Al Khaimah,Al Ain,Sharjah)", "limit": "3000"}), key=lambda p: (p["city"], p["category"] or "")):
    print(f"PL|{p['city']}|{p['category']}|{p['status']}|{p['name']}|{p.get('official_url') or ''}")
