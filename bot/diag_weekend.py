"""Tylko odczyt: wydarzenia na najbliższy weekend (piątek–niedziela) do sprawdzenia u organizatora.
Najpierw jednodniowe i krótkie (do 3 dni), potem reszta zaczynająca się w weekend. Najwyżej 70 linii."""
import os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date()
fri = today + dt.timedelta(days=(4 - today.weekday()) % 7)
sun = fri + dt.timedelta(days=2)
f, s = fri.isoformat(), sun.isoformat()
def cell(x, k=160):
    return str(x if x is not None else "").replace("|", "/").replace("\n", " ")[:k]
ev = db.get("events", {"select": "id,title,start_date,end_date,start_time,end_time,venue,city,category,price_text,is_free,official_url,source_name",
                       "status": "eq.approved", "start_date": f"lte.{s}", "limit": "5000"})
out = []
for r in ev:
    end = r.get("end_date") or r["start_date"]
    if end < f:
        continue
    days = (dt.date.fromisoformat(end) - dt.date.fromisoformat(r["start_date"])).days
    starts = f <= r["start_date"] <= s
    if not starts and days > 3:
        continue   # długie wystawy i sezony – robi je nocna kontrola
    out.append((0 if starts and days <= 3 else 1, r["start_date"], r["city"] or "", r))
out.sort(key=lambda x: x[:3])
print(f"WA|weekend {f}..{s} | events {len(out)}")
for _, _, _, r in out[:70]:
    print("WE|" + "|".join(cell(r.get(k)) for k in ("id", "city", "start_date", "end_date", "start_time", "end_time", "category", "title", "venue", "price_text", "is_free", "official_url", "source_name")))
