"""Tylko odczyt: czy eventy Eid Al Etihad 2026 / festiwale z WhatsAppa już są w bazie."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
KW = ["joubran", "umsiyat", "oven", "motherland", "comitre", "seuss", "pilates", "echoes", "building a life", "arts chat", "kazdoura", "biennial", "souq al mina"]
seen = set()
for k in KW:
    for r in db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,status", "title": f"ilike.*{k}*",
                               "start_date": "gte.2026-11-15", "limit": "40"}):
        if r["id"] in seen: continue
        seen.add(r["id"])
        print(f"F4|{r['status']}|{r['start_date']}..{r.get('end_date') or ''}|{r.get('start_time') or ''}|{r['title']}|{r.get('venue')}|{r['city']}|{r['id']}")
for k in ["smokebreakers", "karma session", "bbq night"]:
    for r in db.get("deals", {"select": "id,title,venue,status", "title": f"ilike.*{k}*", "limit": "10"}):
        print(f"F4|deal|{r['status']}|{r['title']}|{r['venue']}|{r['id']}")
