"""Diagnostyka: szukanie wpisów po słowie (wszystkie statusy)."""
import json, os, sys, requests
URL = os.environ["SUPABASE_URL"].strip(); KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
H = {"apikey": KEY}
for t in ("events", "deals", "places"):
    col = "name" if t == "places" else "title"
    sel = f"id,{col},status,city,start_date,end_date,venue,source_name,gaps,official_url" if t == "events" else f"id,{col},status,city,source_name"
    for q in ("food", "yas"):
        r = requests.get(f"{URL}/rest/v1/{t}", headers=H, params={"select": sel, col: f"ilike.*{q}*", "limit": "100"}, timeout=30)
        for x in r.json():
            print("HIT", t, q, json.dumps(x, ensure_ascii=False))
r = requests.get(f"{URL}/rest/v1/bot_pages", headers=H, params={"select": "url,last_status,last_fetched_at", "url": "ilike.*yas*"}, timeout=30)
print("PAGES", r.text[:800])
