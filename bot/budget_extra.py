"""Jednorazowo 20.11.2026: zgoda właściciela na dodatkowe 5 USD w listopadzie (limit listopada ok. 20 USD). Bez AI."""
import os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
now = dt.datetime.now(dt.timezone.utc)
m0 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
rows = db.get("bot_runs", {"select": "summary", "finished_at": f"gte.{m0}", "summary->>kind": "eq.cost", "limit": "5000"})
if any((r.get("summary") or {}).get("script") == "dodatek listopad" for r in rows):
    print("B|dodatek już jest"); sys.exit(0)
db.insert("bot_runs", {"dry_run": False, "finished_at": now.isoformat(),
                       "summary": {"kind": "cost", "script": "dodatek listopad", "usd": -5.0, "calls": 0, "searches": 0}})
rows = db.get("bot_runs", {"select": "summary", "finished_at": f"gte.{m0}", "summary->>kind": "eq.cost", "limit": "5000"})
print(f"B|stan listopada po dodatku: {sum(float(r['summary'].get('usd') or 0) for r in rows):.2f} / 15 USD")
