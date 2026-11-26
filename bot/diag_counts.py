"""Tylko odczyt: stan bazy – liczby zatwierdzonych / oczekujących pozycji na miasto (CT|)."""
import os, sys, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
t = R.today_uae().isoformat()
ev = db.get("events", {"select": "city,status,start_date,end_date,official_url,start_time", "or": f"(end_date.gte.{t},and(end_date.is.null,start_date.gte.{t}))", "limit": "30000"})
dl = db.get("deals", {"select": "city,status", "limit": "10000"})
pl = db.get("places", {"select": "city,status", "limit": "10000"})
for name, rows in (("events", ev), ("deals", dl), ("places", pl)):
    c = collections.Counter((r["city"], r["status"]) for r in rows)
    st = collections.Counter(r["status"] for r in rows)
    print(f"CT|{name}|" + " ".join(f"{k}:{v}" for k, v in st.items()))
    for city in sorted({r["city"] for r in rows if r.get("city")}):
        print(f"CT|{name}|{city}|approved {c[(city,'approved')]}|pending {c[(city,'pending')]}")
a = [e for e in ev if e["status"] == "approved"]
print(f"CT|events approved upcoming {len(a)}|no link {sum(1 for e in a if not e.get('official_url'))}|no time {sum(1 for e in a if not e.get('start_time'))}")
