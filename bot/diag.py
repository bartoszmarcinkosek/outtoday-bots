import os, requests
URL = os.environ["SUPABASE_URL"].strip()
H = {"apikey": "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"}
E = requests.get(f"{URL}/rest/v1/events?select=title,start_date,venue,city&title=ilike.*candlelight*&start_date=gte.2026-11-16&limit=500", headers=H, timeout=30).json()
for e in E: print("ROW", e["start_date"], "|", e["city"], "|", e["venue"], "|", e["title"])
