import os, sys, json, collections, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
t = R.today_uae(); t14 = (t + dt.timedelta(days=14)).isoformat(); ti = t.isoformat()
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,price_text,official_url,category,gaps", "status": "eq.approved",
                       "or": f"(end_date.gte.{ti},and(end_date.is.null,start_date.gte.{ti}))", "limit": "8000"})
near = [e for e in ev if e["start_date"] <= t14]
print("CV|total upcoming", len(ev), "next14", len(near))
print("CV|" + json.dumps(collections.Counter(e["city"] for e in near).most_common()))
pl = db.get("places", {"select": "city", "status": "eq.approved", "limit": "8000"})
print("CV|places " + json.dumps(collections.Counter(p["city"] for p in pl).most_common()))
dl = db.get("deals", {"select": "city", "status": "eq.approved", "limit": "8000"})
print("CV|deals " + json.dumps(collections.Counter(p["city"] for p in dl).most_common()))
wk = [e for e in ev if e["start_date"] <= "2026-11-22" and (e.get("end_date") or e["start_date"]) >= "2026-11-20"]
print("CV|weekend", len(wk))
for e in wk:
    miss = [k for k in ("venue", "start_time", "price_text") if not e.get(k)]
    if miss: print("WK|" + json.dumps({**{k: e[k] for k in ("id","title","venue","city","start_date","end_date","official_url")}, "miss": miss}, ensure_ascii=False)[:400])
for e in ev:
    if e["start_date"] >= "2026-11-25" and e["start_date"] <= "2027-02-28" and (e.get("end_date") or "") != "":
        print("BIG|" + f'{e["start_date"]}..{e["end_date"]} {e["city"]} | {e["title"]}'[:150])
