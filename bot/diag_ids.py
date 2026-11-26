"""Tylko odczyt: tytuły pozycji o id z audit/show_event_ids.txt. Linie ID|tabela|id|status|miasto|data|tytuł|miejsce|źródło."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ids = [l.split()[0] for l in open(os.path.join(os.path.dirname(__file__), "..", "audit", "show_event_ids.txt")) if l.strip() and not l.startswith("#")]
for t, cols in (("events", "id,status,city,start_date,title,venue,source_name"), ("deals", "id,status,city,valid_until,title,venue,source_name")):
    for r in db.get(t, {"select": cols, "id": f"in.({','.join(ids)})"}):
        print("ID|" + "|".join([t] + [str(r.get(c) or "") for c in cols.split(",")]))
