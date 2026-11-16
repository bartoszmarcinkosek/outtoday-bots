import os, requests, collections
URL = os.environ["SUPABASE_URL"].strip()
KEY = "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"
H = {"apikey": KEY}
P = requests.get(f"{URL}/rest/v1/places?select=*&limit=5000", headers=H, timeout=30).json()
D = requests.get(f"{URL}/rest/v1/deals?select=*&limit=5000", headers=H, timeout=30).json()
E = requests.get(f"{URL}/rest/v1/events?select=city,category,start_date,end_date,start_time,price_text,official_url,url,description&limit=5000", headers=H, timeout=30).json()
E = [e for e in E if (e["end_date"] or e["start_date"]) >= "2026-11-16"]
for name, rows, cat in (("PLACES", P, "category"), ("DEALS", D, "deal_type"), ("EVENTS", E, "category")):
    by = collections.defaultdict(collections.Counter)
    for r in rows: by[r["city"]][r.get(cat)] += 1
    for c, v in by.items(): print(name, c, sum(v.values()), dict(v))
def miss(rows, f): return sum(1 for r in rows if not r.get(f))
print("GAPS places", len(P), {f: miss(P, f) for f in ("official_url", "hours_text", "price_text", "phone", "description", "area")})
print("GAPS deals", len(D), {f: miss(D, f) for f in ("official_url", "price_text", "days_of_week", "start_time", "phone")})
print("GAPS events", len(E), {f: miss(E, f) for f in ("start_time", "price_text", "official_url", "description")})
