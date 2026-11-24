"""Tylko odczyt: zatwierdzone eventy i oferty dodane w ostatnich HOURS godzinach (domyślnie 30).
Do codziennego przeglądu tego, co bot zatwierdził sam. Wypisuje też podejrzane pary (ten sam dzień + miasto + podobny tytuł)."""
import os, sys, re, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
hours = int(os.environ.get("HOURS", "30"))
since = (dt.datetime.utcnow() - dt.timedelta(hours=hours)).strftime("%Y-%m-%dT%H:%M:%S")
today = dt.date.today().isoformat()
def cell(x, n=140):
    return str(x if x is not None else "").replace("|", "/").replace("\n", " ")[:n]
ev = db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,category,price_text,is_free,official_url,source_name,description",
                       "status": "eq.approved", "created_at": f"gte.{since}", "order": "start_date", "limit": "2000"})
print(f"AD|events {len(ev)} since {since}")
for r in ev:
    print("AE|" + "|".join(cell(r.get(k)) for k in ("id", "start_date", "end_date", "start_time", "title", "venue", "city", "category", "price_text", "is_free", "official_url", "source_name", "description")))
dl = db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,start_time,end_time,price_text,official_url,source_name,details",
                      "status": "eq.approved", "created_at": f"gte.{since}", "limit": "2000"})
print(f"AD|deals {len(dl)}")
for r in dl:
    print("AL|" + "|".join(cell(r.get(k)) for k in ("id", "title", "venue", "city", "deal_type", "days_of_week", "start_time", "end_time", "price_text", "official_url", "source_name", "details")))
# możliwe duplikaty: nowe vs wszystkie zatwierdzone tego samego dnia w tym samym mieście
STOP = {"the", "a", "an", "at", "in", "of", "and", "with", "live", "show", "2026", "2027", "uae", "dubai", "abu", "dhabi"}
def words(t):
    return {w for w in re.findall(r"[a-z0-9]+", (t or "").lower()) if len(w) > 2 and w not in STOP}
for r in ev:
    others = db.get("events", {"select": "id,title,start_time,venue", "status": "eq.approved", "city": f"eq.{r['city']}",
                               "start_date": f"eq.{r['start_date']}", "id": f"neq.{r['id']}", "limit": "200"})
    a = words(r["title"])
    for o in others:
        b = words(o["title"])
        if a and b and len(a & b) / min(len(a), len(b)) >= 0.6:
            print(f"DU|{r['id']}|{cell(r['title'],80)}|{r.get('start_time') or ''}|{o['id']}|{cell(o['title'],80)}|{o.get('start_time') or ''}|{cell(o.get('venue'),60)}")
past = [r for r in ev if (r.get("end_date") or r["start_date"]) < today]
print(f"AD|past {len(past)}")
