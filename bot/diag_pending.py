"""Tylko odczyt: wszystkie eventy i oferty czekające na zatwierdzenie (status pending)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,category,price_text,source_name,description,evidence",
                       "status": "eq.pending", "order": "start_date", "limit": "1000"})
print(f"PD|events {len(ev)}")
for r in ev:
    e = r.get("evidence") or {}
    q = (e.get("quote") or e.get("note") or "")[:160] if isinstance(e, dict) else ""
    print("PE|" + "|".join(str(x or "").replace("|", "/").replace("\n", " ")[:140] for x in
          (r["id"], r["start_date"], r.get("end_date"), r.get("start_time"), r["title"], r.get("venue"), r.get("city"), r.get("category"),
           r.get("price_text"), r.get("source_name"), (r.get("description") or "")[:140], q)))
dl = db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,price_text,source_name,details", "status": "eq.pending", "limit": "500"})
print(f"PD|deals {len(dl)}")
for r in dl:
    print("PL|" + "|".join(str(x or "").replace("|", "/").replace("\n", " ")[:140] for x in
          (r["id"], r["title"], r.get("venue"), r.get("city"), r.get("deal_type"), r.get("days_of_week"), r.get("price_text"), r.get("source_name"), (r.get("details") or "")[:140])))
