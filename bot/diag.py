"""Diagnostyka: co widzi apka (ten sam klucz publiczny co apka)."""
import collections, os, requests
URL = os.environ["SUPABASE_URL"].strip()
KEY = "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"
for table, cols in (("events", "city,start_date,end_date"), ("places", "city"), ("deals", "city")):
    r = requests.get(f"{URL}/rest/v1/{table}", params={"select": cols, "limit": "5000"},
                     headers={"apikey": KEY, "Authorization": f"Bearer {KEY}"}, timeout=30)
    print(table, r.status_code, r.text[:200] if r.status_code != 200 else "")
    if r.ok:
        rows = r.json()
        print(" ", len(rows), dict(collections.Counter(x["city"] for x in rows)))
