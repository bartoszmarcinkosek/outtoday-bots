"""REGUŁA (26.11.2026, decyzja właściciela): KONTROLA JAKOŚCI PO KAŻDYM WYSZUKIWANIU.
Uruchamiana automatycznie:
  - po każdym pliku manual/*.json (workflow manual-add.yml): ręczne wyszukiwanie, WhatsApp, zrzuty itd.,
  - po każdym przebiegu botów, które dodają lub poprawiają wpisy (workflow qa-after-bots.yml, tryb SINCE):
    sprawdza wszystko, co powstało lub zmieniło się od startu tego przebiegu.
    Zatwierdzona pozycja z błędem (FAIL) wraca do 'pending' (QA_FIX=1) – znika z apki do mojego przeglądu.
Bez AI, bezpłatna.
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
AGGR = re.compile(r"yalla|timeout(?!market)|whatson\.ae|cobone|groupon|allevents|bayut|propertyfinder|tripadvisor|wego|trip\.com|klook|headout|tiqets|ticketfairy|kidzapp|comingsoon\.ae|running\.life", re.I)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0 Safari/537.36"}
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = R.today_uae()
fails = warns = oks = 0


_CITY_EV = {}  # pamięć: zatwierdzone eventy per miasto (kontrola duplikatów pod innym tytułem)


def out(level, kind, ident, title, msg):
    global fails, warns
    fails += level == "FAIL"; warns += level == "WARN"
    print(f"QA|{level}|{kind}|{ident}|{(title or '')[:70]}|{msg}")


def link_state(u):
    try:
        r = requests.get(u, headers=UA, timeout=12, allow_redirects=True)
        return r.status_code
    except requests.RequestException as e:
        return -404 if re.search(r"NameResolution|getaddrinfo|Name or service not known", str(e)) else 0


def check_link(kind, ident, title, u, need):
    # link do artykułu-listy („Top 20 things to do…”) zamiast strony tej pozycji (Al Jazirah Aviation Club, zgłoszenie 27.11.2026)
    if u and re.search(r"/blog/[^?#]*(top-?\d+|things-to-do|best-|-guide|adventures|sightseeing)|top-\d+-things", u, re.I):
        out("FAIL", kind, ident, title, f"link do artykułu-listy, nie do strony tej pozycji: {u}")
    if SINCE and STATUS.get(ident) != "approved":
        if u and AGGR.search(urlparse(u).netloc):
            out("FAIL", kind, ident, title, f"link do agregatora: {u}")
        return  # oczekujące: link sprawdzam przy przeglądzie, tu tylko agregator
    if not u:
        if need:
            out("WARN", kind, ident, title, "brak linku do organizatora")
        return
    if AGGR.search(urlparse(u).netloc):
        out("FAIL", kind, ident, title, f"link do agregatora: {u}"); return
    st = link_state(u)
    if st in (404, 410, -404):
        out("FAIL", kind, ident, title, f"martwy link ({'domena nie istnieje' if st == -404 else st}): {u}")


SINCE = os.environ.get("SINCE", "").strip()
FIX = os.environ.get("QA_FIX") == "1"
STAT = "in.(approved,pending)" if SINCE else "eq.approved"
fixed = []


def changed(table, cols):
    """Tryb SINCE: wiersze dodane lub zmienione od startu przebiegu bota."""
    try:
        return db.get(table, {"select": cols, "status": STAT, "or": f"(created_at.gte.{SINCE},updated_at.gte.{SINCE})", "limit": "3000"})
    except Exception:
        return db.get(table, {"select": cols, "status": STAT, "created_at": f"gte.{SINCE}", "limit": "3000"})


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
events = db.get("events", {"select": "id,title,city,venue,start_date,end_date,official_url,status,category,description", "id": f"in.({','.join(ev_ids)})"}) if ev_ids else []
for e in new_ev:
    events += [r for r in db.get("events", {"select": "id,title,city,venue,start_date,end_date,official_url,status,category,description",
               "title": f"eq.{e['title']}", "start_date": f"eq.{e['start_date']}"})]
deals = db.get("deals", {"select": "id,title,city,venue,price_text,start_time,official_url,status,source_name,details", "id": f"in.({','.join(dl_ids)})"}) if dl_ids else []
for e in new_dl:
    deals += db.get("deals", {"select": "id,title,city,venue,price_text,start_time,official_url,status,source_name,details", "title": f"eq.{e['title']}", "venue": f"eq.{e.get('venue','')}"})
places = db.get("places", {"select": "id,name,city,official_url,status,category,description", "id": f"in.({','.join(pl_ids)})"}) if pl_ids else []
for p in new_pl:
    places += db.get("places", {"select": "id,name,city,official_url,status,category,description", "name": f"eq.{p['name']}"})

EV_COLS = "id,title,city,venue,start_date,end_date,official_url,status,category,description"
if SINCE:
    events, deals, places = changed("events", EV_COLS), changed("deals", "id,title,city,venue,price_text,start_time,official_url,status,source_name,details"), \
        changed("places", "id,name,city,official_url,status,category,description")
    print(f"QA|INFO|tryb SINCE {SINCE}: events {len(events)}, deals {len(deals)}, places {len(places)}")

# bramka: nowe pozycje z pliku czekają jako "pending" i są sprawdzane jak zatwierdzone (także link)
_gf = os.environ.get("QA_GATE_FILE", "")
GATE = {}
if _gf and os.path.exists(_gf):
    if _gf.endswith(".jsonl"):
        for _l in open(_gf):
            if _l.strip():
                _r = json.loads(_l); GATE.setdefault(_r["t"], []).append(_r["id"])
    else:
        GATE = json.load(open(_gf))
GATE_IDS = {i for ids in GATE.values() for i in ids}
for x in events + deals + places:
    if x["id"] in GATE_IDS:
        x["status"] = "approved"
failed = set()
_out = out


def out(level, kind, ident, title, msg):  # noqa: F811 – przy FIX zatwierdzona pozycja z FAIL wraca do pending
    _out(level, kind, ident, title, msg)
    if level == "FAIL":
        failed.add(ident)
    if level == "FAIL" and FIX and ident not in fixed and STATUS.get(ident) == "approved":
        fixed.append(ident)
        db.update({"event": "events", "deal": "deals", "place": "places"}[kind], {"id": ident}, {"status": "pending"})
        print(f"QA|FIXED|{kind}|{ident}|wraca do pending")


_cache = {}


def _city(table, cols, city):
    if (table, city) not in _cache:
        _cache[(table, city)] = db.get(table, {"select": cols, "status": "eq.approved", "city": f"eq.{city}", "limit": "3000"})
    return _cache[(table, city)]


STATUS = {x["id"]: x["status"] for x in events + deals + places}

# pary sprawdzone ręcznie: podobne nazwy, ale to różne rzeczy (audit/qa_not_dupes.txt: "id1 id2 # opis")
_nd = os.path.join(os.path.dirname(__file__), "..", "audit", "qa_not_dupes.txt")
NOT_DUPES = {frozenset(l.split()[:2]) for l in (open(_nd) if os.path.exists(_nd) else []) if len(l.split()) >= 2 and not l.startswith("#")}
# miejsca za granicą w tytule / miejscu wydarzenia; globalni organizatorzy wędrówek (dają wydarzenia z całego świata)
FOREIGN_RE = r"\b(australia|melbourne|sydney|\bvic\b|lebanon|beirut|ehmej|macedon|amman|wadi rum|egypt|cairo|sinai|saudi|riyadh|jeddah|alula|bahrain|manama|kuwait|tbilisi|armenia|yerevan|nepal|kathmandu|kilimanjaro|tanzania|kenya|morocco|marrakech|atlas mountains|istanbul|cappadocia|croatia|zagreb)\b"
GLOBAL_ORG_RE = r"highlanderadventure\.com"
UAE_RE = r"\b(uae|emirates|dubai|abu dhabi|sharjah|ajman|ras al khaimah|rak|fujairah|umm al quwain|al ain|hatta|jebel jais|jais|khor ?fakkan|kalba|dibba|liwa|al dhafra|mleiha)\b"
# numer terminu na końcu tytułu: „29/1”, „(9–10 Dec)”, „– 12 Dec”, „(Day 2)”, „Show 2”, „Ripe Market -4”
SESSION_RE = re.compile(r"\s*(\(\s*\d{1,2}(\s*[–-]\s*\d{1,2})?\s*[a-z]{3,9}\.?\s*\)|\(\s*[a-z]{3,9}\s+\d{1,2}(\s*[–-]\s*\d{1,2})?\s*\)|\b\d{1,2}/\d{1,2}(/\d{2,4})?|[–-]\s*\d{1,2}\s+[a-z]{3,9}|\(?\b(day|show|session|part)\s*\d\)?|\s[–-]\s?\d{1,2})\s*$", re.I)
for e in {x["id"]: x for x in events}.values():
    if e["status"] not in ("approved", "pending") or (not SINCE and e["status"] != "approved"):
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
        if o["id"] != e["id"] and o["start_date"] == e["start_date"] and R.titles_match(o["title"], e["title"]) \
                and frozenset((o["id"], e["id"])) not in NOT_DUPES:
            out("FAIL", "event", e["id"], e["title"], f"możliwy duplikat: {o['id']} '{o['title'][:50]}' {o['start_date']}")
    # ten sam wydarzenie dwa razy z różnymi datami: ta sama strona biletów + podobny tytuł (Lamhayab ft. Yassar Lemghari:
    # 25.12 i 9.01 – strona Platinumlist podaje tylko 25.12; tester 27.11.2026). Druga data pochodzi z błędnego odczytu.
    if e.get("official_url") and re.search(r"platinumlist|virginmegastore|ticketmaster|coca-cola-arena|etihadarena|dubaiopera", e["official_url"], re.I):
        for o in db.get("events", {"select": "id,title,start_date", "status": "eq.approved", "official_url": f"eq.{e['official_url']}", "limit": "20"}):
            if o["id"] != e["id"] and o["start_date"] != e["start_date"] and R.titles_match(o["title"], e["title"]) \
                    and frozenset((o["id"], e["id"])) not in NOT_DUPES:
                out("FAIL", "event", e["id"], e["title"], f"ten sam bilet co {o['id']} ({o['start_date']}) – jedna z dat jest błędna albo połącz w jedną kartę")
                break
    # wydarzenie za granicą (Highlander: Mount Macedon w Australii, Ehmej w Libanie, wpisane jako Ras Al Khaimah – tester 26.11.2026)
    _txt = f"{e['title']} {e.get('venue') or ''}"
    if re.search(FOREIGN_RE, e.get("venue") or "", re.I) or (re.search(GLOBAL_ORG_RE, e.get("official_url") or "", re.I)
                                             and not re.search(UAE_RE, f"{_txt} {e.get('description') or ''}", re.I)):
        out("FAIL", "event", e["id"], e["title"], "wydarzenie poza ZEA (miejsce za granicą albo globalny organizator bez miejsca w ZEA)")
    # ten sam spektakl rozbity na osobne karty dla każdego terminu („… 29/1”, „… 30/1”; „Peter Pan (9–10 Dec)” i „(11–12 Dec)”)
    _stem = SESSION_RE.sub("", e["title"]).strip(" –-")
    # (też identyczny tytuł w tym samym miejscu 1–3 dni później: Hansel & Gretel 9.12 i 10.12 jako dwie karty)
    same_venue = db.get("events", {"select": "id,title,start_date,venue", "status": "eq.approved", "city": f"eq.{e['city']}",
                                   "venue": f"eq.{e.get('venue')}", "start_date": f"gte.{(sd - dt.timedelta(days=7)).isoformat()}", "limit": "200"}) if e.get("venue") else []
    for o in same_venue:
        if o["start_date"] > (sd + dt.timedelta(days=7)).isoformat():
            continue
        if o["id"] != e["id"] and o.get("venue") == e.get("venue") and o["start_date"] != e["start_date"] and frozenset((o["id"], e["id"])) not in NOT_DUPES:
            _same = SESSION_RE.sub("", o["title"]).strip(" –-").lower() == _stem.lower()
            if (_same and _stem.lower() != e["title"].strip().lower()) or (o["title"].strip().lower() == e["title"].strip().lower()
                    and abs((dt.date.fromisoformat(o["start_date"]) - sd).days) <= 3):
                out("FAIL", "event", e["id"], e["title"], f"ten sam spektakl jako osobna karta na każdy termin: {o['id']} {o['start_date']} – połącz w jedną kartę (od–do)")
                break
    # ten sam event dwa razy pod trochę innym tytułem i z inną datą w tym samym miejscu („Tony Robbins BREAKTHROUGH” 24.04.2027
    # i „Tony Robbins Breakthrough 2027” z błędną datą 10–11.12 – tester A 27.11.2026): tytuł bez roku i wielkości liter
    if e.get("venue"):
        # pełna kontrola bazy 27.11.2026: „Phantom of the Opera Abu Dhabi” 17.04 vs „Phantom of the Opera” 10.03, „Andre/André Rieu”,
        # „Charlie and the Chocolate Factory” vs „…: The Musical”, „Youssou N'DOUR/N'Dour” – ten sam event, druga data błędna.
        # Inny zapis tytułu = inne źródło = duplikat z błędną datą -> FAIL (ukryte do sprawdzenia). Identyczny tytuł = cykl -> tylko WARN.
        import unicodedata
        def _norm(t):
            t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
            t = re.sub(r"\b(20\d\d|the musical|musical|live|in concert|the|in (abu dhabi|dubai|sharjah|al ain|ras al khaimah)|abu dhabi|dubai)\b|&|\band\b", " ", t)
            return re.sub(r"[^a-z0-9]", "", t)
        _vk = lambda v: re.sub(r"[^a-z]", "", (v or "").lower().split(",")[0].split("·")[0])[:12]
        if e["city"] not in _CITY_EV:
            _CITY_EV[e["city"]] = db.get("events", {"select": "id,title,start_date,end_date,venue", "status": "eq.approved", "city": f"eq.{e['city']}", "limit": "3000"})
        for o in _CITY_EV[e["city"]]:
            if o["id"] == e["id"] or o["start_date"] == e["start_date"] or _vk(o.get("venue")) != _vk(e.get("venue")) or frozenset((o["id"], e["id"])) in NOT_DUPES:
                continue
            if _norm(o["title"]) and _norm(o["title"]) == _norm(e["title"]):
                ov = o["start_date"] <= (e.get("end_date") or e["start_date"]) and e["start_date"] <= (o.get("end_date") or o["start_date"])
                lvl = "FAIL" if (o["title"].strip() != e["title"].strip() and not ov) else "WARN"
                out(lvl, "event", e["id"], e["title"], f"ten sam event pod innym zapisem tytułu w tym samym miejscu: {o['id']} '{o['title'][:40]}' {o['start_date']} – jedna z dat jest błędna, sprawdź u organizatora")
                break
    # słowo WIELKIMI LITERAMI w tytule (BREAKTHROUGH, IMAGINARY … KRASOTA) – tester A 27.11.2026
    if re.search(r"\b[A-Z]{8,}\b", e["title"]):
        out("WARN", "event", e["id"], e["title"], "słowo WIELKIMI LITERAMI w tytule – zapisz normalnie")
    # tytuł z wyciętym separatorem (kilka spacji: „Yaw Owusu   Where The Tide Flows”) – stare wpisy sprzed poprawki w run.py (tester 27.11.2026)
    if re.search(r"\S {2,}\S", e["title"]):
        out("FAIL", "event", e["id"], e["title"], "tytuł z kilkoma spacjami (wycięty separator) – wstaw „ – ”")
    # separator „|” albo „\” w tytule (Alserkal „Faris Alshafar | Everybody…”, „Saturday Run \ Al Heera Beach” – tester B 27.11.2026)
    if re.search(r"\s[|\\]\s|\s[|\\]|[|\\]\s", e["title"]):
        out("FAIL", "event", e["id"], e["title"], "separator „|” lub „\\” w tytule – wstaw „ – ”")
    # godzina w tytule („Board game night …, 6 PM”) – godzina należy do pola start_time (tester B 27.11.2026)
    if re.search(r",?\s\d{1,2}(:\d{2})?\s?(am|pm)\s*$", e["title"], re.I):
        out("WARN", "event", e["id"], e["title"], "godzina w tytule – przenieś do start_time")
    # brak opisu = nie wiadomo, o co chodzi (Ghostly Kisses, zgłoszenie 27.11.2026). Nowe pozycje: FAIL (ukryte do uzupełnienia), stare: WARN
    if len((e.get("description") or "").strip()) < 40:
        out("FAIL" if (SINCE or e["id"] in GATE_IDS) else "WARN", "event", e["id"], e["title"], "brak opisu albo za krótki (<40 znaków) – dopisz 1–2 zdania ze strony organizatora")
    # promocje sklepów i centrów handlowych to nie wydarzenia (zasada właściciela; „12-Day Super Sale” w Reem Mall, 26.11.2026)
    if re.search(r"\b(super |mega |big |flash |mid[- ]season |year[- ]end |summer |winter |clearance )?sales?\b|\d+\s?% off|\bdiscounts?\b|\bshopping festival offers?\b", e["title"], re.I) \
            and not re.search(r"book (sale|fair)|garage sale|car boot|yard sale|charity", e["title"], re.I):
        out("FAIL", "event", e["id"], e["title"], "promocja/wyprzedaż, nie wydarzenie")
    # długie wydarzenie, które jest stałym miejscem z apki (La Perle jako miejsce i jako „wydarzenie do 31.12”, zgłoszenie 26.11.2026)
    if (ed - sd).days >= 14:
        for o in _city("places", "id,name", e["city"]):
            nm = (o["name"] or "").strip()
            if len(nm) >= 6 and re.match(re.escape(nm) + r"\b", e["title"], re.I) and frozenset((o["id"], e["id"])) not in NOT_DUPES:
                out("FAIL", "event", e["id"], e["title"], f"to samo co stałe miejsce: {o['id']} '{nm}'")
                break
    check_link("event", e["id"], e["title"], e.get("official_url"), True)
    oks += 1

for d in {x["id"]: x for x in deals}.values():
    if d["status"] not in ("approved", "pending") or (not SINCE and d["status"] != "approved"):
        continue
    if not d.get("price_text") and not d.get("start_time"):
        out("FAIL", "deal", d["id"], d["title"], "oferta bez ceny i bez godziny")
    if d.get("city") not in CITIES:
        out("FAIL", "deal", d["id"], d["title"], f"miasto spoza listy: {d.get('city')}")
    # brak miejsca albo urwana nazwa („Dubai Marina)”): karta nie mówi, gdzie to jest (tester A 28.11 – Cargo, Crafty Fox, Nuri)
    _v = (d.get("venue") or "").strip()
    if not _v or _v.count("(") != _v.count(")"):
        out("FAIL" if (SINCE or d["id"] in GATE_IDS) else "WARN", "deal", d["id"], d["title"], f"brak miejsca albo urwana nazwa miejsca: '{_v}'")
    same = _city("deals", "id,title,venue", d["city"])
    for o in same:
        if o["id"] != d["id"] and R.norm(o.get("venue") or "")[:20] == R.norm(d.get("venue") or "")[:20] and R.titles_match(o["title"], d["title"]):
            out("FAIL", "deal", d["id"], d["title"], f"możliwy duplikat: {o['id']} '{o['title'][:50]}'")
    # oferta tylko z przewodnika/portalu, bez strony lokalu, albo z dopiskiem „confirm before you go” = niepotwierdzona (27.11.2026)
    if (not (d.get("official_url") or "").strip() and re.search(r"time ?out|yalla|what'?s ?on|the national|kidzapp|best bites|cobone|groupon|curly ?tales", d.get("source_name") or "", re.I)) \
            or re.search(r"confirm before you go|sources differ|listed (in )?20\d\d", f"{d.get('details') or ''} {d.get('price_text') or ''}", re.I):
        out("FAIL", "deal", d["id"], d["title"], "niepotwierdzona u lokalu (tylko portal / stara lista) – potwierdź na stronie lub IG lokalu")
    check_link("deal", d["id"], d["title"], d.get("official_url"), False)
    oks += 1

# pary sprawdzone ręcznie: podobne nazwy, ale to różne miejsca (audit/qa_not_dupes.txt: "id1 id2 # opis")
for p in {x["id"]: x for x in places}.values():
    if p["status"] not in ("approved", "pending") or (not SINCE and p["status"] != "approved"):
        continue
    same = _city("places", "id,name", p["city"])
    for o in same:
        if o["id"] != p["id"] and frozenset((o["id"], p["id"])) not in NOT_DUPES and R.titles_match(o["name"], p["name"]):
            out("FAIL", "place", p["id"], p["name"], f"możliwy duplikat: {o['id']} '{o['name'][:50]}'")
    check_link("place", p["id"], p["name"], p.get("official_url"), False)
    oks += 1

for tbl, ids in GATE.items():
    for i in ids:
        if i in failed:
            print(f"QA|HELD|{tbl}|{i}|nie przeszło kontroli – zostaje niewidoczne (pending)")
        else:
            db.update(tbl, {"id": i}, {"status": "approved"})
            print(f"QA|PASSED|{tbl}|{i}|przeszło kontrolę – widoczne w apce")
print(f"QA|SUMMARY|checked {oks}|fail {fails}|warn {warns}|back to pending {len(fixed)}")
# w trybie botów błąd już naprawiony (pozycja ukryta) – run nie jest czerwony; ręczne dodanie – czerwony, poprawiam od razu
# zatrzymane przez kontrolę (ukryte do poprawy) to nie awaria – bez czerwonego wyniku i e-maila (decyzja właściciela 27.11.2026);
# czerwono tylko, gdy błąd został, a nic go nie ukryło (przegląd bez QA_FIX)
sys.exit(1 if fails and not FIX else 0)
