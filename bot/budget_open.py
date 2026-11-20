"""Jednorazowo (20.11.2026): bilans otwarcia budżetu AI za bieżący miesiąc z dotychczasowych wpisów bot_runs
(zanim koszty zaczęły być zapisywane jako summary.kind = 'cost'). Bez AI."""
import os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
now = dt.datetime.now(dt.timezone.utc)
m0 = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
rows = db.get("bot_runs", {"select": "finished_at,summary", "finished_at": f"gte.{m0}", "limit": "5000"})
if any((r.get("summary") or {}).get("script") == "bilans otwarcia" for r in rows):
    print("bilans już jest"); sys.exit(0)
usd = 0.0
for r in rows:
    s = r.get("summary") or {}
    if s.get("kind") == "cost":
        continue
    u = s.get("usage") or {}
    usd += u.get("input", 0) * 0.10 / 1e6 + u.get("output", 0) * 0.50 / 1e6 + (u.get("searches") or 0) * 0.01
usd += 1.64 + 0.43 + 0.22  # Fill links 20.11 + Fill time and price 19.11 i 20.11 (te skrypty nie zapisywały kosztu)
db.insert("bot_runs", {"dry_run": False, "finished_at": now.isoformat(),
                       "summary": {"kind": "cost", "script": "bilans otwarcia", "usd": round(usd, 2), "calls": 0, "searches": 0}})
print(f"B|bilans otwarcia {now:%Y-%m}: {usd:.2f} USD")
