import os, requests, collections
URL = os.environ["SUPABASE_URL"].strip()
KEY = "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"
H = {"apikey": KEY}
P = requests.get(f"{URL}/rest/v1/places?select=city,category,official_url,hours_text&limit=5000", headers=H, timeout=30).json()
D = requests.get(f"{URL}/rest/v1/deals?select=city,deal_type,official_url&limit=5000", headers=H, timeout=30).json()
print("PLACES", len(P), dict(collections.Counter(p["city"] for p in P)))
print("PLACES Dubai", dict(collections.Counter(p["category"] for p in P if p["city"] == "Dubai")))
print("DEALS", len(D), dict(collections.Counter(d["city"] for d in D)))
print("DEALS Dubai", dict(collections.Counter(d["deal_type"] for d in D if d["city"] == "Dubai")))
print("NO_URL deals", sum(1 for d in D if not d.get("official_url")), "places", sum(1 for p in P if not p.get("official_url")), "NO_HOURS places", sum(1 for p in P if not p.get("hours_text")))
