"""Tylko odczyt: wiersz day pass Aloft Abu Dhabi i Bungee at Yas Bay."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for t, f, q in (("deals", "title", "*Aloft Abu Dhabi*"), ("deals", "venue", "*Aloft Abu Dhabi*"), ("places", "name", "*Bungee*")):
    for r in db.get(t, {"select": "*", f: f"ilike.{q}", "limit": "10"}):
        print("F3|" + t + "|" + json.dumps({k: v for k, v in r.items() if v not in (None, "", [], {})}, ensure_ascii=False)[:1500])
