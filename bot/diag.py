import os, requests, collections, json
URL = os.environ["SUPABASE_URL"].strip(); KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
H = {"apikey": KEY}
rows = requests.get(f"{URL}/rest/v1/bot_changes", headers=H, params={"select": "*", "handled": "eq.false", "limit": "1000"}, timeout=30).json()
print("TOTAL", len(rows))
c = collections.Counter((r["table_name"], r["field"], bool(r.get("evidence"))) for r in rows)
for k, v in c.most_common(): print("KIND", k, v)
for r in rows[:25]:
    print("EX", r["table_name"], r["field"], repr(r["old_value"])[:40], "->", repr(r["new_value"])[:50], "|", (r.get("evidence") or "")[:60], "|", (r.get("source_url") or "")[:50])
