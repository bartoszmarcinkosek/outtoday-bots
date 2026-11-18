import os, sys, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ti = R.today_uae().isoformat()
CITIES = {"Abu Dhabi","Al Ain","Dubai","Sharjah","Ajman","Umm Al Quwain","Ras Al Khaimah","Fujairah"}
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,price_text,is_free,description,category", "status": "eq.approved",
                       "or": f"(end_date.gte.{ti},and(end_date.is.null,start_date.gte.{ti}))", "limit": "8000"})
print(f"L|EVENTS {len(ev)}")
def key(t): return re.sub(r"[^a-z0-9]", "", (t or "").lower())[:40]
g = collections.defaultdict(list)
for e in ev: g[(key(e["title"]), e["start_date"])].append(e)
d = [v for v in g.values() if len(v) > 1]
print(f"L|DUP {len(d)}")
for v in d[:40]: print("L|  dup", v[0]["start_date"], v[0]["title"][:60], "|", " / ".join((x.get("venue") or "")[:25]+" "+x["id"][:8] for x in v))
bc = [e for e in ev if e.get("city") not in CITIES]; print(f"L|BADCITY {len(bc)}")
for e in bc[:20]: print("L|  city", repr(e.get("city")), e["title"][:60], e["id"][:8])
caps = [e for e in ev if re.sub(r"[^A-Za-z]","",e["title"]) and re.sub(r"[^A-Za-z]","",e["title"]).isupper() and len(e["title"])>8]; print(f"L|CAPS {len(caps)}")
for e in caps[:20]: print("L|  caps", e["title"][:70], e["id"][:8])
nonen = [e for e in ev if re.search(r"[؀-ۿЀ-ӿ]", e["title"])]; print(f"L|NONLATIN {len(nonen)}")
for e in nonen[:20]: print("L|  lang", e["title"][:70], e["id"][:8])
nodesc = [e for e in ev if len((e.get("description") or "").strip()) < 30]; print(f"L|NODESC {len(nodesc)}")
for e in nodesc[:15]: print("L|  desc", e["start_date"], e["title"][:60], e["id"][:8])
notime = [e for e in ev if not e.get("start_time") and not e.get("end_date")]; print(f"L|NOTIME(single-day) {len(notime)}")
noprice = [e for e in ev if not e.get("price_text") and not e.get("is_free")]; print(f"L|NOPRICE {len(noprice)}")
long = [e for e in ev if e.get("end_date") and (R.dt.date.fromisoformat(e["end_date"]) - R.dt.date.fromisoformat(e["start_date"])).days > 120]; print(f"L|LONG>120d {len(long)}")
for e in long[:15]: print("L|  long", e["start_date"], e["end_date"], e["title"][:55], e["id"][:8])
for t, cols in (("places","id,name,city,area,status"), ("deals","id,title,venue,city,status")):
    rows = db.get(t, {"select": cols, "status": "eq.approved", "limit": "8000"})
    g = collections.defaultdict(list)
    for r in rows: g[(key(r.get("name") or r.get("title")), key(r.get("venue") or r.get("area") or ""), r.get("city"))].append(r)
    d = [v for v in g.values() if len(v) > 1]
    print(f"L|{t.upper()} {len(rows)} DUP {len(d)}")
    for v in d[:20]: print("L|  dup", (v[0].get("name") or v[0].get("title"))[:55], v[0].get("city"), " ".join(x["id"][:8] for x in v))
    bc = [r for r in rows if r.get("city") not in CITIES]; print(f"L|  badcity {len(bc)}", [ (r.get('city'), (r.get('name') or r.get('title'))[:30]) for r in bc[:8]])
