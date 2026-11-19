import os, requests, datetime as dt
url = os.environ["SUPABASE_URL"].rstrip("/") + "/rest/v1"
k = os.environ["SUPABASE_SECRET_KEY"]
h = {"apikey": k, "Prefer": "count=exact", "Range": "0-0"}
if not k.startswith("sb_"): h["Authorization"] = f"Bearer {k}"
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date().isoformat()
for t, q in (("events", {}), ("events", {"status": "eq.approved"}),
             ("events", {"status": "eq.approved", "or": f"(end_date.gte.{today},and(end_date.is.null,start_date.gte.{today}))"}),
             ("places", {"status": "eq.approved"}), ("deals", {"status": "eq.approved"})):
    r = requests.get(f"{url}/{t}", headers=h, params={"select": "id", **q}, timeout=30)
    print("ROW", t, q, r.headers.get("content-range"))
