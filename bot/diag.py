import json, os, requests
URL = os.environ["SUPABASE_URL"].strip(); KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
r = requests.get(f"{URL}/rest/v1/events", headers={"apikey": KEY}, params={"select": "*", "title": "ilike.*taste of*"}, timeout=30)
for x in r.json():
    x.pop("evidence", None); print("ROW", json.dumps(x, ensure_ascii=False))
