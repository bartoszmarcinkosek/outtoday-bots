import os, datetime as dt
import run as R
db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=6)).isoformat()
rows = db.get("bot_runs", {"select": "finished_at,summary", "finished_at": f"gte.{since}", "order": "finished_at", "limit": "500"})
for r in rows:
    s = r.get("summary") or {}; u = s.get("usage") or {}
    src = s.get("sources") or []
    names = [x.get("name") if isinstance(x, dict) else str(x) for x in (src if isinstance(src, list) else list(src))][:2]
    usd = (u.get("input", 0) or 0) / 1e6 * 0.10 + (u.get("output", 0) or 0) / 1e6 * 0.50 + (u.get("searches", 0) or 0) * 0.01
    print("ROW", r["finished_at"][:16], s.get("kind") or "-", "src", len(src), names, "calls", u.get("calls"), "srch", u.get("searches"), f"${usd:.2f}", list(s.get("counts", {}).keys())[:4] if isinstance(s.get("counts"), dict) else "")
