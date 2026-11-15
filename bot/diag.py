"""Diagnostyka: co widzi apka (klucz publiczny = tylko zatwierdzone)."""
import collections, os, requests
URL = os.environ["SUPABASE_URL"].strip()
KEY = "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
for table in ("events", "places", "deals"):
    r = requests.get(f"{URL}/rest/v1/{table}?select=city&limit=5000", headers=H, timeout=30)
    rows = r.json() if r.ok else []
    print("COUNT", table, len(rows), dict(collections.Counter(x["city"] for x in rows)))
