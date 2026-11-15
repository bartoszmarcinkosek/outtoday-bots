"""Diagnostyka: pending eventy spoza Abu Dhabi (z kluczem serwisowym)."""
import json, os, requests
URL = os.environ["SUPABASE_URL"].strip()
KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
H = {"apikey": KEY}
r = requests.get(f"{URL}/rest/v1/events", headers=H, timeout=30, params={
    "select": "id,title,city,venue,area,start_date,end_date,start_time,price_text,status,source_name,gaps,official_url,url,evidence",
    "status": "eq.pending", "order": "city,start_date", "limit": "1000"})
print("STATUS", r.status_code, r.text[:200] if not r.ok else "")
rows = r.json()
print("PENDING", len(rows))
for x in rows:
    if (x["city"] or "").lower().startswith("abu") or "al ain" in (x["city"] or "").lower():
        continue
    ev = x.pop("evidence") or {}
    x["q"] = {k: (v[:160] if isinstance(v, str) else v) for k, v in ev.items() if k in ("date", "time", "price", "venue", "quote", "auto")} if isinstance(ev, dict) else None
    print("ROW", json.dumps(x, ensure_ascii=False))
