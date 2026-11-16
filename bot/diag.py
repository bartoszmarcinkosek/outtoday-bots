import os, requests, collections
URL = os.environ["SUPABASE_URL"].strip()
KEY = "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"
rows = requests.get(f"{URL}/rest/v1/events?select=city,venue,area,start_date,end_date&limit=5000", headers={"apikey": KEY}, timeout=30).json()
today = "2026-11-16"
up = [r for r in rows if (r["end_date"] or r["start_date"]) >= today]
def city(r):
    t = " ".join(str(r.get(k) or "") for k in ("city", "venue", "area")).lower()
    c = (r["city"] or "").lower()
    if "al ain" in t and ("abu" in c or "al ain" in c): return "Al Ain"
    return r["city"]
print("COUNT total", len(rows), "upcoming", len(up), dict(collections.Counter(city(r) for r in up)))
