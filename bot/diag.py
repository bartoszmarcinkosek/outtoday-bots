import os, requests
URL = os.environ["SUPABASE_URL"].strip()
H = {"apikey": "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"}
P = requests.get(f"{URL}/rest/v1/places?select=id,name,city,category,area,description&limit=5000", headers=H, timeout=30).json()
for p in sorted(P, key=lambda p:(p["category"] or "", p["city"])):
    if p["category"] in ("markets","malls","shopping","markets_malls") or "mall" in (p["category"] or "") or "market" in (p["category"] or "") or "mall" in p["name"].lower():
        print("ROW", p["id"], "|", p["city"], "|", p["category"], "|", p["name"], "|", (p["description"] or "")[:90])
