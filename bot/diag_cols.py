"""Tylko odczyt: kolumny tabel (CL|)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for t in ("deals", "places", "events"):
    r = db.get(t, {"select": "*", "limit": "1"})
    print(f"CL|{t}|" + ",".join(sorted(r[0].keys())) if r else f"CL|{t}|-")
