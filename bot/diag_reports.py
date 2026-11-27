"""Tylko odczyt: zgłoszenia z apki (tabela suggestions) z ostatnich HOURS godzin (domyślnie 30)."""
import os, sys, json, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
since = (dt.datetime.utcnow() - dt.timedelta(hours=int(os.environ.get("HOURS", "30")))).strftime("%Y-%m-%dT%H:%M:%S")
rows = db.get("suggestions", {"select": "*", "created_at": f"gte.{since}", "order": "created_at.desc", "limit": "100"})
rows = [r for r in rows if not (r.get("title") or "").startswith("AppError:")]  # błędy apki czyta diag_errors.py
print(f"RA|suggestions since {since}: {len(rows)}")
for r in rows:
    print("RP|" + json.dumps({k: v for k, v in r.items() if v not in (None, "", [])}, ensure_ascii=False).replace("\n", " ")[:900])
