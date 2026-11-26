"""Tylko odczyt: zatwierdzone nadchodzące wydarzenia bez godziny startu – podział (NT|) i lista jednodniowych (NL|)."""
import os, sys, collections, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
t = R.today_uae()
ev = db.get("events", {"select": "id,title,city,category,start_date,end_date,start_time,official_url,source_name,venue", "status": "eq.approved",
                       "start_time": "is.null", "or": f"(end_date.gte.{t},and(end_date.is.null,start_date.gte.{t}))", "limit": "5000"})
def kind(e):
    sd = dt.date.fromisoformat(e["start_date"]); ed = dt.date.fromisoformat(e["end_date"]) if e.get("end_date") else sd
    n = (ed - sd).days
    return "1 dzien" if n == 0 else "2-7 dni" if n <= 7 else "8-60 dni" if n <= 60 else "ponad 60 dni"
c = collections.Counter(kind(e) for e in ev)
print("NT|razem", len(ev), "|", dict(c))
one = [e for e in ev if kind(e) in ("1 dzien", "2-7 dni")]
print("NT|krotkie (1-7 dni):", len(one), "| z linkiem", sum(1 for e in one if e.get("official_url")),
      "| w ciagu 14 dni", sum(1 for e in one if dt.date.fromisoformat(e["start_date"]) <= t + dt.timedelta(days=14)))
print("NT|zrodla krotkich:", collections.Counter((e.get("source_name") or "-")[:25] for e in one).most_common(12))
print("NT|kategorie krotkich:", collections.Counter(e["category"] for e in one).most_common())
for e in sorted(one, key=lambda x: x["start_date"])[:200]:
    print(f"NL|{e['id']}|{e['city']}|{e['start_date']}|{e.get('end_date') or ''}|{e['category']}|{e['title'][:60]}|{(e.get('venue') or '')[:40]}|{e.get('official_url') or ''}")
