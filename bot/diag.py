"""Diagnostyka: dokładnie te same zapytania co apka."""
import collections, os, requests
URL = os.environ["SUPABASE_URL"].strip()
KEY = "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
for table, order in (("events", "start_date.asc,start_time.asc.nullslast"), ("places", "name.asc"), ("deals", "title.asc")):
    r = requests.get(f"{URL}/rest/v1/{table}?select=*&order={order}", headers=H, timeout=30)
    print(table, r.status_code, len(r.content), r.text[:300] if r.status_code != 200 else "")
    if r.ok:
        rows = r.json()
        print("  ", len(rows), dict(collections.Counter(x.get("city") for x in rows)))
