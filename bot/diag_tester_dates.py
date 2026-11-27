"""Tylko odczyt, bez AI (dla testera kart): daty i opisy zatwierdzonych wydarzeń oraz data dodania wszystkich pozycji.
Linie: ED|id|start|end|created|długość opisu|opis (200 zn.)   CR|tabela|id|created"""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for e in db.get("events", {"select": "id,start_date,end_date,created_at,description", "status": "eq.approved", "limit": "5000"}):
    d = re.sub(r"\s+", " ", e.get("description") or "").replace("|", "/")
    print(f"ED|{e['id']}|{e['start_date']}|{e.get('end_date') or ''}|{(e.get('created_at') or '')[:10]}|{len(d)}|{d[:200]}")
for t in ("deals", "places"):
    for r in db.get(t, {"select": "id,created_at", "status": "eq.approved", "limit": "5000"}):
        print(f"CR|{t}|{r['id']}|{(r.get('created_at') or '')[:10]}")
