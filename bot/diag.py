import os, requests
URL = os.environ["SUPABASE_URL"].strip(); KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
H = {"apikey": KEY, "Content-Type": "application/json"}
r = requests.get(f"{URL}/rest/v1/events", headers=H, params={"select": "id,title,status,bot_key", "bot_key": "like.eventbrite:*"}, timeout=30)
rows = r.json()
for x in rows: print("ROW", x["status"], x["title"][:60], x["id"])
# duplikaty SAT03: zostaw odrzucony, usuń nowszy pending
for x in rows:
    if x["title"].startswith("SAT03") and x["status"] == "pending":
        requests.patch(f"{URL}/rest/v1/events", headers=H, params={"id": f"eq.{x['id']}"}, json={"status": "rejected"}, timeout=30)
        print("REJECTED duplicate", x["id"])
