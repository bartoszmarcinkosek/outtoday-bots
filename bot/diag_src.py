"""Tylko odczyt: skąd pochodzą pozycje z audit/show_ids.txt (źródło, link, dowód, daty)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ids = [l.split()[0] for l in open(os.path.join(os.path.dirname(__file__), "..", "audit", "show_ids.txt")) if l.strip()]
for r in db.get("deals", {"select": "*", "id": "in.(" + ",".join(ids) + ")"}):
    keep = {k: r.get(k) for k in ("title", "source_name", "official_url", "evidence", "created_at", "verified_at", "valid_until", "details") if r.get(k) not in (None, "", [])}
    print("SRC|" + json.dumps(keep, ensure_ascii=False)[:900])
