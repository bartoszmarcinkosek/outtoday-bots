"""Tylko odczyt: grupy duplikatów odrzucone dziś przez nocną kontrolę – czy miały inne godziny."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("events", {"select": "id,title,start_date,start_time,venue,city,status,updated_at", "updated_at": "gte.2026-11-23T14:00:00Z",
                         "status": "eq.rejected", "limit": "200"})
for r in rows:
    same = db.get("events", {"select": "id,start_time,status", "start_date": f"eq.{r['start_date']}", "city": f"eq.{r['city']}",
                             "venue": f"eq.{r.get('venue')}", "status": "eq.approved", "limit": "20"}) if r.get("venue") else []
    times = sorted({str(x.get("start_time")) for x in same})
    print(f"F6|{r['start_date']}|{r.get('start_time')}|{r['title'][:60]}|kept_times={times}|{r['id']}")
