"""Tylko odczyt: ile wydarzeń dało każde źródło (events.source_name) – łącznie i w ostatnich 14 dniach.
Linie SY|id|miasto|nazwa|łącznie|14 dni  tylko dla źródeł, które w 14 dni nie dały nic; SA| podsumowanie."""
import os, sys, json, glob, collections, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
since = (dt.datetime.utcnow() - dt.timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%S")
tot, rec = collections.Counter(), collections.Counter()
for off in range(0, 40000, 1000):
    page = db.get("events", {"select": "source_name,created_at", "order": "id", "limit": "1000", "offset": str(off)})
    for r in page:
        tot[r.get("source_name") or ""] += 1
        if (r.get("created_at") or "") >= since:
            rec[r.get("source_name") or ""] += 1
    if len(page) < 1000:
        break
srcs = []
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "sources", "*.json"))):
    d = json.load(open(f))
    if isinstance(d, dict) and isinstance(d.get("sources"), list):
        srcs += d["sources"]
dead = [s for s in srcs if rec[s.get("name") or ""] == 0]
print(f"SA|sources {len(srcs)} | nothing in 14 days {len(dead)} | never anything {sum(1 for s in dead if tot[s.get('name') or ''] == 0)}")
for s in sorted(dead, key=lambda s: (tot[s.get("name") or ""], s.get("city") or "")):
    print(f"SY|{s.get('id')}|{s.get('city')}|{s.get('name')}|{tot[s.get('name') or '']}|0|{(s.get('urls') or [''])[0]}")
