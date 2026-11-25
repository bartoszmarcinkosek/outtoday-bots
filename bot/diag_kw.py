"""Tylko odczyt: szuka w wydarzeniach / miejscach / dealach po słowach z audit/find_kw.txt (jedno w linii) – przed ręcznym dodaniem, żeby nie zrobić duplikatu."""
import os, sys, json, re, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
kw = [l.strip() for l in open(os.path.join(os.path.dirname(__file__), "..", "audit", "find_kw.txt"), encoding="utf-8") if l.strip() and not l.startswith("#")]
since = (R.today_uae() - dt.timedelta(days=20)).isoformat()
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,status,category,official_url,price_text,is_free",
                       "or": f"(end_date.gte.{since},and(end_date.is.null,start_date.gte.{since}))", "limit": "20000"})
pl = db.get("places", {"select": "id,name,area,city,status,category", "limit": "5000"})
dl = db.get("deals", {"select": "id,title,venue,city,status,deal_type,days_of_week,start_time,end_time,price_text,valid_until", "limit": "5000"})
for k in kw:
    rx = re.compile(re.escape(k), re.I)
    m = [e for e in ev if rx.search((e.get("title") or "") + " " + (e.get("venue") or ""))]
    print(f"KW|{k}|events {len(m)}")
    for e in sorted(m, key=lambda x: x["start_date"])[:14]:
        print("KW|  E " + json.dumps({a: e[a] for a in ("id", "start_date", "end_date", "start_time", "status", "city", "category", "title", "venue", "price_text", "official_url") if e.get(a) not in (None, "")}, ensure_ascii=False)[:330])
    for d in [d for d in dl if rx.search((d.get("title") or "") + " " + (d.get("venue") or ""))][:10]:
        print("KW|  D " + json.dumps({a: d[a] for a in d if d.get(a) not in (None, "", [])}, ensure_ascii=False)[:330])
    for p in [p for p in pl if rx.search((p.get("name") or "") + " " + (p.get("area") or ""))][:8]:
        print("KW|  P " + json.dumps(p, ensure_ascii=False)[:260])
