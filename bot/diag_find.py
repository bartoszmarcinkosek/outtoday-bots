import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ti = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,status,official_url", "status": "in.(approved,pending)",
                       "or": f"(end_date.gte.{ti},and(end_date.is.null,start_date.gte.{ti}))", "limit": "8000"})
KW = ["Guggenheim","Shopping Festival","DSF","Al Hosn","Liwa","Global Village","Grand Prix","Rugby","Sevens","National Day","Eid Al Etihad","Marathon","Dubai Run","Ride","Fitness Challenge","Light Festival","Marmoom","New Year","Fireworks","Mother of the Nation","Hatta","Jazz","Camel","Christmas","Festive","Biennial","Design Week","Tennis","DP World","Golf","Dhafra","Zayed Festival","Heritage","Air Show","Airshow","Food Festival","Taste of","Comic Con","Coldplay","Ed Sheeran","Andrea Bocelli"]
for k in KW:
    m = [e for e in ev if re.search(re.escape(k), e["title"], re.I)]
    print(f"F|{k}: {len(m)}")
    for e in m[:6]: print(f"F|   {e['start_date']}..{e.get('end_date')} {e['city']} [{e['status']}] {e['title']}"[:160])
cities = sorted({e["city"] for e in ev})
print("F|cities " + json.dumps(cities, ensure_ascii=False))
for e in ev:
    if re.search(r"nader", e["title"], re.I): print("F|NADER " + json.dumps(e, ensure_ascii=False)[:300])
