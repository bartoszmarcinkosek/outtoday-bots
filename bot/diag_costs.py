import os, sys, json, collections, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=8)).isoformat()
runs = db.get("bot_runs", {"select": "finished_at,summary", "finished_at": f"gte.{since}", "order": "finished_at.asc", "limit": "500"})
P_IN, P_OUT, P_S = 0.10/1e6, 0.50/1e6, 0.01
for r in runs:
    s = r.get("summary") or {}; u = s.get("usage") or {}
    c = u.get("input",0)*P_IN + u.get("output",0)*P_OUT + u.get("searches",0)*P_S
    print("RUN|", r["finished_at"][:16], f"${c:.2f}", "calls", u.get("calls"), "in", u.get("input"), "out", u.get("output"), "search", u.get("searches"), "|", json.dumps({k: v for k, v in s.items() if k != "usage"})[:200])
