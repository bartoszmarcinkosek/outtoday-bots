"""Szuka eventów/ofert po słowach (sprawdzanie duplikatów przed ręcznym dodaniem)."""
import os, run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for w in ["Night Market", "Emirates Villages", "Villages Run", "Al Rams", "Shuwaib", "Bandar"]:
    for e in db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,status", "title": f"ilike.*{w}*", "limit": "10"}):
        print("E", w, "|", e)
for w in ["Cove", "Basilico", "Smoke"]:
    for e in db.get("deals", {"select": "id,title,venue,city,deal_type,status", "or": f"(title.ilike.*{w}*,venue.ilike.*{w}*)", "limit": "10"}):
        print("D", w, "|", e)
