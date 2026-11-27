"""Tylko odczyt: wydarzenia startujące za 8–30 dni do porównania ze stroną organizatora (decyzja właściciela 27.11.2026).
Pomija sprawdzone w ostatnich 14 dniach (audit/upcoming_checked.json). Najpierw duże (koncerty, festiwale, sport), najwyżej 80 linii."""
import os, sys, json, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date()
a, b = (today + dt.timedelta(days=8)).isoformat(), (today + dt.timedelta(days=30)).isoformat()
try:
    seen = json.load(open(os.path.join(os.path.dirname(__file__), "..", "audit", "upcoming_checked.json")))
except Exception:
    seen = {}
lim = (today - dt.timedelta(days=14)).isoformat()
def cell(x, k=160):
    return str(x if x is not None else "").replace("|", "/").replace("\n", " ")[:k]
ev = db.get("events", {"select": "id,title,start_date,end_date,start_time,end_time,venue,city,category,price_text,is_free,official_url,source_name",
                       "status": "eq.approved", "start_date": f"gte.{a}", "and": f"(start_date.lte.{b})", "limit": "5000"})
BIG = {"music": 0, "festivals": 0, "sport": 1}
rows = [r for r in ev if seen.get(r["id"], "") < lim and r.get("official_url")]
rows.sort(key=lambda r: (BIG.get(r.get("category"), 2), r["start_date"]))
print(f"UA|{a}..{b} | events {len(ev)} | to check {len(rows)}")
for r in rows[:80]:
    print("UE|" + "|".join(cell(r.get(k)) for k in ("id", "city", "start_date", "end_date", "start_time", "end_time", "category", "title", "venue", "price_text", "is_free", "official_url", "source_name")))
