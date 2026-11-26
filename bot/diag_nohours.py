"""Tylko odczyt: zatwierdzone miejsca bez godzin otwarcia (NH|id|city|cat|name|url)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
pl = db.get("places", {"select": "id,city,category,name,hours_text,official_url,verified_at", "status": "eq.approved", "limit": "5000"})
no = [p for p in pl if not (p.get("hours_text") or "").strip()]
print(f"NS|places {len(pl)}|no hours {len(no)}|verified {sum(1 for p in pl if p.get('verified_at'))}")
for p in sorted(no, key=lambda p: (p["city"] or "", p["category"] or "")):
    print(f"NH|{p['id']}|{p['city']}|{p['category']}|{p['name']}|{p.get('official_url') or ''}")
