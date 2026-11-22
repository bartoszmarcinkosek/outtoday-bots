"""Tylko odczyt: licznik użycia apki (app_stats) – ostatnie 7 dni."""
import os, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("app_stats", {"select": "day,name,value,city,platform", "order": "day.desc", "limit": "50000"})
print(f"ST|wierszy: {len(rows)}")
for (d, n), c in sorted(Counter((r["day"], r["name"]) for r in rows).items(), reverse=True)[:60]:
    print(f"ST|{d}|{n}|{c}")
for v, c in Counter(f'{r["name"]}:{r.get("value")}:{r.get("city")}' for r in rows).most_common(40):
    print(f"ST|top|{v}|{c}")
