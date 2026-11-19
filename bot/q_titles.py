"""Szuka eventów po słowach w tytule (sprawdzanie duplikatów przed ręcznym dodaniem)."""
import os, run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for w in ["Golden", "Choral", "Building a Life", "Curating the Commons", "Acid Arab", "Open Studio", "Gurel", "Coastal Narratives", "Public Art Abu Dhabi", "Biennial"]:
    for e in db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,status", "title": f"ilike.*{w}*", "start_date": "gte.2026-11-01", "limit": "10"}):
        print(w, "|", e)
