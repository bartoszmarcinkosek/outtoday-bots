import os, requests
URL = os.environ["SUPABASE_URL"].strip()
H = {"apikey": "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"}
D = requests.get(f"{URL}/rest/v1/deals?select=title,venue,city,deal_type&deal_type=eq.day_pass&limit=5000", headers=H, timeout=30).json()
for d in sorted(D, key=lambda d:(d["city"], d["venue"] or "")): print("ROW", d["city"], "|", d["venue"], "|", d["title"])
E = requests.get(f"{URL}/rest/v1/events?select=title,venue,status,source_name&source_name=ilike.*meetup*&limit=500", headers=H, timeout=30).json()
print("MEETUP", len(E))
for e in E: print("MROW", e["title"], "|", e["venue"])
