"""REGUŁA (26.11.2026, decyzja właściciela): KONTROLA JAKOŚCI PO KAŻDYM WYSZUKIWANIU.
Uruchamiana automatycznie po każdym pliku manual/*.json (workflow manual-add.yml), czyli po każdym dodaniu
lub poprawce z ręcznego wyszukiwania, WhatsAppa, zrzutów itd. Bez AI, bezpłatna.
Dla każdej pozycji z pliku (nowej i poprawianej) sprawdza:
  - duplikat: to samo wydarzenie / oferta / miejsce już zatwierdzone pod inną nazwą (ten sam dzień i miasto),
  - daty: początek w przeszłości, koniec przed początkiem, rok w tytule inny niż rok wydarzenia,
  - link: brak (wydarzenia), agregator zamiast organizatora, strona nie istnieje (404, martwa domena),
  - podstawy: miasto spoza listy, kategoria, oferta bez ceny i bez godziny.
Linie: QA|FAIL|... (do naprawy od razu), QA|WARN|... (do sprawdzenia), QA|OK|liczba. Przy FAIL run kończy się błędem,
żeby było go widać na liście runów."""
import datetime as dt, json, os, re, sys
from urllib.parse import urlparse
sys.path.insert(0, os.path.dirname(__file__))
import requests
import run as R

CITIES = {"Abu Dhabi", "Al Ain", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"}
AGGR = re.compile(r"yalla|timeout|whatson\.ae|cobone|groupon|allevents|bayut|propertyfinder|tripadvisor|wego|trip\.com|klook|headout|tiqets|ticketfairy|kidzapp|comingsoon\.ae|running\.life", re.I)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = R.today_uae()
fails = warns = oks = 0


def out(level, kind, ident, title, msg):
    global fails, warns
    fails += level == "FAIL"; warns += level == "WARN"
    print(f"QA|{level}|{kind}|{ident}|{(title or '')[:70]}|{msg}")


def link_state(u):
    try:
        r = requests.get(u, headers=UA, timeout=20, allow_redirects=True)
        return r.status_code
    except requests.RequestException as e:
        return -404 if re.search(r"NameResolution|getaddrinfo|Name or service not known", str(e)) else 0


def check_link(kind, ident, title, u, need):
    if not u:
        if need:
            out("WARN", kind, ident, title, "brak linku do organizatora")
        return
    if AGGR.search(urlparse(u).netloc):
        out("FAIL", kind, ident, title, f"link do agregatora: {u}"); return
    st = link_state(u)
    if st in (404, 410, -404):
        out("FAIL", kind, ident, title, f"martwy link ({'domena nie istnieje' if st == -404 else st}): {u}")


files = [f for f in os.environ.get("FILES", "").split() if f.startswith("manual/") and f.endswith(".json") and os.path.exists(f)]
ev_ids, dl_ids, pl_ids = set(), set(), set()
new_ev, new_dl, new_pl = [], [], []
for path in files:
    d = json.load(open(path, encoding="utf-8"))
    new_ev += d.get("events", []); new_dl += d.get("deals", []); new_pl += d.get("places", [])
    ev_ids |= {u["id"] for u in d.get("update_event_ids", [])}
    dl_ids |= {u["id"] for u in d.get("update_deal_ids", [])}
    pl_ids |= {u["id"] for u in d.get("update_place_ids", [])}
    rejected = set(d.get("reject_event_ids", [])) | set(d.get("reject_deal_ids", [])) | set(d.get("reject_places", []))
    ev_ids -= rejected; dl_ids -= rejected; pl_ids -= rejected

# wiersze z bazy: poprawiane po id, nowe po tytule
events = db.get("events", {"select": "id,title,city,venue,start_date,end_date,official_url,status,category", "id": f"in.({','.join(ev_ids)})"}) if ev_ids else []
for e in new_ev:
    events += [r for r in db.get("events", {"select": "id,title,city,venue,start_date,end_date,official_url,status,category",
               "title": f"eq.{e['title']}", "start_date": f"eq.{e['start_date']}"})]
deals = db.get("deals", {"select": "id,title,city,venue,price_text,start_time,official_url,status", "id": f"in.({','.join(dl_ids)})"}) if dl_ids else []
for e in new_dl:
    deals += db.get("deals", {"select": "id,title,city,venue,price_text,start_time,official_url,status", "title": f"eq.{e['title']}", "venue": f"eq.{e.get('venue','')}"})
places = db.get("places", {"select": "id,name,city,official_url,status,category", "id": f"in.({','.join(pl_ids)})"}) if pl_ids else []
for p in new_pl:
    places += db.get("places", {"select": "id,name,city,official_url,status,category", "name": f"eq.{p['name']}"})

for e in {x["id"]: x for x in events}.values():
    if e["status"] != "approved":
        continue
    try:
        sd = dt.date.fromisoformat(e["start_date"]); ed = dt.date.fromisoformat(e["end_date"]) if e.get("end_date") else sd
    except Exception:
        out("FAIL", "event", e["id"], e["title"], "zła data"); continue
    if ed < today:
        out("FAIL", "event", e["id"], e["title"], f"wydarzenie już minęło ({e['start_date']}–{e.get('end_date')})")
    if ed < sd:
        out("FAIL", "event", e["id"], e["title"], "koniec przed początkiem")
    yrs = re.findall(r"\b(20\d\d)\b", e["title"])
    if yrs and str(sd.year) not in yrs and str(ed.year) not in yrs:
        out("WARN", "event", e["id"], e["title"], f"rok w tytule {yrs} ≠ rok wydarzenia {sd.year}")
    if e.get("city") not in CITIES:
        out("FAIL", "event", e["id"], e["title"], f"miasto spoza listy: {e.get('city')}")
    # duplikaty: zatwierdzone wydarzenia w tym samym mieście, nachodzące daty, podobny tytuł
    near = db.get("events", {"select": "id,title,start_date,end_date,venue", "status": "eq.approved", "city": f"eq.{e['city']}",
                             "start_date": f"lte.{ed.isoformat()}", "or": f"(end_date.gte.{sd.isoformat()},and(end_date.is.null,start_date.gte.{sd.isoformat()}))", "limit": "500"})
    for o in near:
        # ten sam dzień startu + podobny tytuł = duplikat; inny dzień to zwykle osobny punkt programu festiwalu
        if o["id"] != e["id"] and o["start_date"] == e["start_date"] and R.titles_match(o["title"], e["title"]):
            out("FAIL", "event", e["id"], e["title"], f"możliwy duplikat: {o['id']} '{o['title'][:50]}' {o['start_date']}")
    check_link("event", e["id"], e["title"], e.get("official_url"), True)
    oks += 1

for d in {x["id"]: x for x in deals}.values():
    if d["status"] != "approved":
        continue
    if not d.get("price_text") and not d.get("start_time"):
        out("FAIL", "deal", d["id"], d["title"], "oferta bez ceny i bez godziny")
    if d.get("city") not in CITIES:
        out("FAIL", "deal", d["id"], d["title"], f"miasto spoza listy: {d.get('city')}")
    same = db.get("deals", {"select": "id,title,venue", "status": "eq.approved", "city": f"eq.{d['city']}", "limit": "2000"})
    for o in same:
        if o["id"] != d["id"] and R.norm(o.get("venue") or "")[:20] == R.norm(d.get("venue") or "")[:20] and R.titles_match(o["title"], d["title"]):
            out("FAIL", "deal", d["id"], d["title"], f"możliwy duplikat: {o['id']} '{o['title'][:50]}'")
    check_link("deal", d["id"], d["title"], d.get("official_url"), False)
    oks += 1

for p in {x["id"]: x for x in places}.values():
    if p["status"] != "approved":
        continue
    same = db.get("places", {"select": "id,name", "status": "eq.approved", "city": f"eq.{p['city']}", "limit": "2000"})
    for o in same:
        if o["id"] != p["id"] and R.titles_match(o["name"], p["name"]):
            out("FAIL", "place", p["id"], p["name"], f"możliwy duplikat: {o['id']} '{o['name'][:50]}'")
    check_link("place", p["id"], p["name"], p.get("official_url"), False)
    oks += 1

print(f"QA|SUMMARY|checked {oks}|fail {fails}|warn {warns}")
sys.exit(1 if fails else 0)
