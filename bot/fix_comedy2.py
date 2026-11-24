"""Jednorazowo: kategoria comedy -> music (stand-upy razem w Music & Shows)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("events", {"select": "id", "category": "eq.comedy", "limit": "2000"})
for r in rows:
    db.update("events", {"id": r["id"]}, {"category": "music"})
print(f"FC|comedy -> music: {len(rows)}")
