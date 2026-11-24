"""Tylko odczyt: czego ludzie szukali w apce bez wyniku (app_stats name=search, value '0|fraza') – ostatnie DAYS dni (domyślnie 14)."""
import os, sys, collections, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
since = (R.today_uae() - dt.timedelta(days=int(os.environ.get("DAYS", "14")))).isoformat()
rows = db.get("app_stats", {"select": "day,value,city", "name": "eq.search", "day": f"gte.{since}", "limit": "50000"})
zero, ok = collections.Counter(), collections.Counter()
for r in rows:
    v = (r.get("value") or "")
    kind, _, q = v.partition("|")
    (zero if kind == "0" else ok)[q.strip().lower()] += 1
print(f"SQ|since {since} searches {len(rows)} zero {sum(zero.values())} ok {sum(ok.values())}")
for q, n in zero.most_common(60):
    print(f"S0|{n}|{q}")
for q, n in ok.most_common(25):
    print(f"S1|{n}|{q}")
