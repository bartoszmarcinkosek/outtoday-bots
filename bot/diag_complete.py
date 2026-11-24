"""Tylko odczyt: kompletność danych w zatwierdzonych, nadchodzących wpisach."""
import os, sys, datetime as dt, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = dt.date.today().isoformat()
ev = [e for e in db.get("events", {"select": "*", "status": "eq.approved", "limit": "8000"}) if (e.get("end_date") or e["start_date"]) >= today]
def pct(n, t): return f"{n} ({round(100*n/max(t,1))}%)"
n = len(ev)
print(f"C|events {n}|bez godziny {pct(sum(1 for e in ev if not e.get('start_time')), n)}|bez ceny i nie free {pct(sum(1 for e in ev if not e.get('price_text') and not e.get('is_free')), n)}|bez opisu {pct(sum(1 for e in ev if not (e.get('description') or '').strip()), n)}|bez linku {pct(sum(1 for e in ev if not e.get('official_url')), n)}|bez miejsca {pct(sum(1 for e in ev if not e.get('venue')), n)}|bez wsp. {pct(sum(1 for e in ev if e.get('lat') is None), n)}")
print("C|events miasta " + str(collections.Counter(e["city"] for e in ev).most_common()))
print("C|events kategorie " + str(collections.Counter(e.get("category") for e in ev).most_common()))
far = sum(1 for e in ev if e["start_date"] > (dt.date.today() + dt.timedelta(days=60)).isoformat())
wk = sum(1 for e in ev if e["start_date"] <= (dt.date.today() + dt.timedelta(days=7)).isoformat())
print(f"C|events w ciągu 7 dni {wk}|dalej niż 60 dni {far}")
dl = db.get("deals", {"select": "*", "status": "eq.approved", "limit": "5000"})
n = len(dl)
print(f"C|deals {n}|bez ceny {pct(sum(1 for d in dl if not d.get('price_text')), n)}|bez godzin {pct(sum(1 for d in dl if not d.get('start_time')), n)}|bez dni {pct(sum(1 for d in dl if not d.get('days_of_week')), n)}|bez linku {pct(sum(1 for d in dl if not d.get('official_url')), n)}|bez wsp. {pct(sum(1 for d in dl if d.get('lat') is None), n)}")
print("C|deals miasta " + str(collections.Counter(d["city"] for d in dl).most_common()))
old = sum(1 for d in dl if (d.get("verified_at") or d.get("updated_at") or d.get("created_at") or "")[:10] < (dt.date.today() - dt.timedelta(days=45)).isoformat())
print(f"C|deals niesprawdzane >45 dni {pct(old, n)}")
pl = db.get("places", {"select": "*", "status": "eq.approved", "limit": "5000"})
n = len(pl)
print(f"C|places {n}|bez godzin {pct(sum(1 for p in pl if not p.get('hours_text')), n)}|bez ceny {pct(sum(1 for p in pl if not p.get('price_text') and not p.get('is_free')), n)}|bez wsp. {pct(sum(1 for p in pl if p.get('lat') is None), n)}")
print("C|places miasta " + str(collections.Counter(p["city"] for p in pl).most_common()))
