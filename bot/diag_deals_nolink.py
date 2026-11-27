"""Tylko odczyt: zatwierdzone oferty bez linku (DL|id|city|deal_type|title|venue|price_text|details|source)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("deals", {"select": "id,city,deal_type,title,venue,price_text,details,source_name,official_url", "status": "eq.approved", "limit": "5000"})
for r in rows:
    if not (r.get("official_url") or "").strip():
        print("DL|" + "|".join(str(r.get(k) or "").replace("|", "/").replace("\n", " ")[:150] for k in ("id", "city", "deal_type", "title", "venue", "price_text", "details", "source_name")))
