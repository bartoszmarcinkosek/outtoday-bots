import os, requests, collections
URL = os.environ["SUPABASE_URL"].strip()
H = {"apikey": "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"}
D = requests.get(f"{URL}/rest/v1/deals?select=title,venue,city&deal_type=eq.brunch&limit=5000", headers=H, timeout=30).json()
print("BRUNCH", dict(collections.Counter(d["city"] for d in D)))
for d in sorted(D, key=lambda d:(d["city"], d["venue"] or "")):
    if d["city"] != "Abu Dhabi": print("ROW", d["city"], "|", d["venue"], "|", d["title"])
