"""Tylko odczyt: wszystkie wydarzenia 26.11–7.12.2026 związane z Eid Al Etihad / świętem (słowa kluczowe), wg emiratu."""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,status,official_url",
    "or": "(and(start_date.gte.2026-11-20,start_date.lte.2026-12-07),and(end_date.gte.2026-11-26,start_date.lte.2026-12-07))", "limit": "5000"})
rx = re.compile(r"eid|etihad|national day|union|flag|drone|firework|parade|fursan|55|watan|nation", re.I)
for e in sorted(ev, key=lambda x: (x["city"], x["start_date"])):
    if rx.search(e["title"] + " " + (e.get("venue") or "")):
        print(f"EID|{e['city']}|{e['start_date']}..{e.get('end_date') or ''}|{(e.get('start_time') or '')[:5]}|{e['status'][:3]}|{e['title'][:75]}|{(e.get('venue') or '')[:40]}|{e['id'][:8]}")
