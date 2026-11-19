import os, json, datetime as dt, collections
import run as R
db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=14)).isoformat()
rows = db.get("bot_runs", {"select": "finished_at,summary,dry_run", "finished_at": f"gte.{since}", "order": "finished_at", "limit": "1000"})
tot = collections.defaultdict(lambda: [0, 0, 0, 0, 0])
for r in rows:
    s = r.get("summary") or {}
    u = s.get("usage") or {}
    kind = s.get("kind") or ("events" if "sources" in s else "?")
    k = (r["finished_at"][:10], kind)
    t = tot[k]
    t[0] += 1; t[1] += u.get("input", 0) or 0; t[2] += u.get("output", 0) or 0; t[3] += u.get("searches", 0) or 0; t[4] += u.get("calls", 0) or 0
for (d, kind), (n, i, o, srch, c) in sorted(tot.items()):
    usd = i / 1e6 * 0.10 + o / 1e6 * 0.50 + srch * 0.01
    print(d, kind, "runs", n, "calls", c, "in", i, "out", o, "search", srch, f"${usd:.3f}")
print("keys sample", [list((r.get('summary') or {}).keys())[:6] for r in rows[-3:]])
