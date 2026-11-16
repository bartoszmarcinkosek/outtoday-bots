import os, requests
URL = os.environ["SUPABASE_URL"].strip(); KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
H = {"apikey": KEY, "Content-Type": "application/json"}
r = requests.patch(f"{URL}/rest/v1/bot_changes", headers={**H, "Prefer": "return=representation"},
                   params={"handled": "eq.false", "field": "eq.venue", "table_name": "eq.events"}, json={"handled": True}, timeout=30)
print("IGNORED", len(r.json()) if r.ok else r.text[:200])
