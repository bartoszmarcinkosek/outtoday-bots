"""Przegląd jakości: zatwierdzone wpisy z typowymi błędami."""
import os, re, sys, json, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,price_text,category,source_name",
                       "status": "eq.approved", "or": f"(end_date.gte.{today},and(end_date.is.null,start_date.gte.{today}))", "limit": "6000"})
pl = db.get("places", {"select": "id,name,area,city,category,price_text", "status": "eq.approved", "limit": "3000"})
dl = db.get("deals", {"select": "id,title,venue,city,deal_type,price_text,valid_until,days_of_week,source_name", "status": "eq.approved", "limit": "3000"})
print("COUNTS", len(ev), len(pl), len(dl))
NONLAT = re.compile(r"[Ѐ-ӿ؀-ۿऀ-ॿ一-鿿]")
def out(tag, row): print(tag + "|" + json.dumps(row, ensure_ascii=False)[:330])
for kind, rows, t, v in (("E", ev, "title", "venue"), ("P", pl, "name", "area"), ("D", dl, "title", "venue")):
    for r in rows:
        tt, vv = r.get(t) or "", r.get(v) or ""
        why = []
        if NONLAT.search(tt + vv): why.append("nonlatin")
        if vv and vv == vv.lower() and re.search("[a-z]", vv): why.append("venue-lower")
        if len(tt) > 12 and tt == tt.upper() and re.search("[A-Z]{4}", tt): why.append("title-caps")
        if tt == tt.lower() and re.search("[a-z]", tt): why.append("title-lower")
        if re.search(r"https?://|www\.|goo\.gl", vv) or len(vv) > 90: why.append("venue-long")
        if re.search(r"\b(test|tbc|tba|lorem)\b", tt, re.I): why.append("tbc")
        if why: out(kind + ":" + ",".join(why), {"id": r["id"], t: tt, v: vv, "city": r.get("city")})
# duplikaty
c = collections.defaultdict(list)
for e in ev:
    c[(R.norm(e["title"])[:40], e["start_date"], e["city"])].append(e)
for k, rows in c.items():
    if len(rows) > 1: out("DUPE_E", [{"id": x["id"], "title": x["title"], "venue": x["venue"], "src": x["source_name"]} for x in rows])
c = collections.defaultdict(list)
for d in dl:
    c[(R.norm(d["title"])[:30], R.norm(d.get("venue") or "")[:25], d["city"])].append(d)
for k, rows in c.items():
    if len(rows) > 1: out("DUPE_D", [{"id": x["id"], "title": x["title"], "venue": x["venue"]} for x in rows])
c = collections.defaultdict(list)
for p in pl:
    c[(R.norm(p["name"])[:30], p["city"])].append(p)
for k, rows in c.items():
    if len(rows) > 1: out("DUPE_P", [{"id": x["id"], "name": x["name"]} for x in rows])
for d in dl:
    if d.get("valid_until") and d["valid_until"] < today: out("D:expired", {"id": d["id"], "title": d["title"], "vu": d["valid_until"]})
for d in dl:
    if re.search(r"christmas|festive|new year|nye|diwali|halloween|thanksgiving|ramadan|iftar|eid|valentine|national day", d["title"], re.I):
        out("D:seasonal", {"id": d["id"], "title": d["title"], "venue": d["venue"], "vu": d.get("valid_until")})
