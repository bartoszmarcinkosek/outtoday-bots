import os, requests
URL = os.environ["SUPABASE_URL"].strip(); KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
for r in requests.get(f"{URL}/rest/v1/bot_changes", headers={"apikey": KEY}, params={"select": "old_value,new_value", "handled": "eq.false"}, timeout=30).json():
    print("V", repr(r["old_value"])[:60], "->", repr(r["new_value"])[:70])
