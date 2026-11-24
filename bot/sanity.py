"""OutToday: darmowa kontrola spójności danych (bez AI). Tylko odczyt – wypisuje podejrzane pozycje.
Linie: S|kod|tabela|id|miasto|tytuł|szczegół.  Uruchamianie: diag.yml z inputs[script]=sanity (codzienny przegląd je czyta)."""
from __future__ import annotations
import collections, datetime as dt, math, os, re, sys
from urllib.parse import urlparse
sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402
from geocode import CITY, km  # noqa: E402

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = R.today_uae()
T = today.isoformat()
out: list[tuple] = []


def add(code, table, r, detail=""):
    title = r.get("title") or r.get("name") or ""
    out.append((code, table, r["id"], r.get("city") or "", str(title).replace("|", "/")[:70], str(detail).replace("|", "/").replace("\n", " ")[:120]))


ev = db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,category,price_text,is_free,official_url,description,lat,lng",
                       "status": "eq.approved", "or": f"(end_date.gte.{T},start_date.gte.{T})", "limit": "5000"})
dl = db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,start_time,end_time,price_text,valid_until,official_url,details,lat,lng",
                      "status": "eq.approved", "limit": "5000"})
pl = db.get("places", {"select": "id,name,city,category,hours_text,price_text,is_free,official_url,description,lat,lng",
                       "status": "eq.approved", "limit": "5000"})
print(f"SA|events {len(ev)} deals {len(dl)} places {len(pl)}")

AED = re.compile(r"(aed|dhs?|dirham)\s*\d|\d\s*(aed|dhs?|dirham)", re.I)
FREEWORD = re.compile(r"\bfree\b|no charge|complimentary", re.I)
CAPS = lambda t: len(t) > 12 and sum(c.isupper() for c in t) / max(1, sum(c.isalpha() for c in t)) > 0.8
AGG = ("yallaabudhabi", "timeoutdubai", "timeoutabudhabi", "cobone", "groupon", "whatson.ae", "tripadvisor", "wow-rak", "koobit", "google.", "facebook.com/events/search")

for r in ev:
    sd, ed = r["start_date"], r.get("end_date")
    if ed and ed < sd:
        add("END_BEFORE_START", "events", r, f"{sd} -> {ed}")
    if ed and (dt.date.fromisoformat(ed) - dt.date.fromisoformat(sd)).days > 120:
        add("LONG_EVENT", "events", r, f"{sd} -> {ed}")
    m = re.search(r"\b(20\d\d)\b", r.get("title") or "")
    if m and int(m.group(1)) < int(sd[:4]) and not re.search(r"20\d\d\s*[/-]\s*\d\d", r["title"]):
        add("OLD_YEAR_IN_TITLE", "events", r, sd)
    if r.get("start_time") in ("00:00", "00:00:00"):
        add("MIDNIGHT_START", "events", r, r.get("venue"))
for table, rows in (("events", ev), ("places", pl)):
    for r in rows:
        p = r.get("price_text") or ""
        if r.get("is_free") and AED.search(p) and not FREEWORD.search(p):
            add("FREE_BUT_PRICE", table, r, p)
        if not r.get("is_free") and re.match(r"\s*free\b(?! (flow|drink))", p, re.I) and not AED.search(p):
            add("PRICE_SAYS_FREE", table, r, p)
for r in dl:
    vu = r.get("valid_until")
    if vu and vu < T:
        add("DEAL_EXPIRED", "deals", r, vu)
    if r.get("start_time") and r.get("start_time") == r.get("end_time"):
        add("SAME_START_END", "deals", r, r["start_time"])
    if not r.get("price_text") and not r.get("start_time"):
        add("DEAL_NO_PRICE_NO_TIME", "deals", r, r.get("venue"))
for table, rows, dcol in (("events", ev, "description"), ("deals", dl, "details"), ("places", pl, "description")):
    for r in rows:
        t = r.get("title") or r.get("name") or ""
        if CAPS(t):
            add("CAPS_TITLE", table, r)
        d = (r.get(dcol) or "").strip()
        if len(d) > 60 and not re.search(r"[.!?)\"'’”…]$", d):
            add("CUT_TEXT", table, r, "…" + d[-50:])
        if r.get("city") not in CITY:
            add("BAD_CITY", table, r, r.get("city"))
        u = r.get("official_url") or ""
        if u and any(a in urlparse(u).netloc.lower() + urlparse(u).path.lower() for a in AGG):
            add("AGGREGATOR_LINK", table, r, u)
        if u and not u.startswith("http"):
            add("BAD_LINK", table, r, u)
        # współrzędne
        if r.get("lat") is None or r.get("city") not in CITY:
            continue
        pt = (r["lat"], r["lng"])
        if not (22.5 <= pt[0] <= 26.5 and 51.0 <= pt[1] <= 56.7):
            add("GEO_OUTSIDE_UAE", table, r, pt)
            continue
        own = km(pt, CITY[r["city"]])
        near, nd = min(((c, km(pt, xy)) for c, xy in CITY.items()), key=lambda x: x[1])
        if near != r["city"] and own > 25 and own - nd > 12:
            add("GEO_OTHER_EMIRATE", table, r, f"{r.get('venue') or ''} | pin near {near} ({nd:.0f} km), {own:.0f} km from {r['city']}")

# to samo miejsce (ta sama nazwa i miasto) z pinezkami oddalonymi o ponad 2 km
byv = collections.defaultdict(list)
for table, rows in (("events", ev), ("deals", dl), ("places", pl)):
    for r in rows:
        v = re.sub(r"[^a-z0-9 ]", "", (r.get("venue") or r.get("name") or "").lower()).strip()
        if r.get("lat") is not None and len(v) > 5:
            byv[(r.get("city"), v)].append((table, r))
for (c, v), lst in byv.items():
    a = lst[0][1]
    for table, b in lst[1:]:
        d = km((a["lat"], a["lng"]), (b["lat"], b["lng"]))
        if d > 2:
            add("PIN_MISMATCH", table, b, f"{v}: {d:.1f} km from the pin of another item at the same venue ({a['id']})")
            break

# ta sama pinezka dla wielu różnych miejsc (geokoder trafił w środek dzielnicy)
pins = collections.defaultdict(set)
ref = {}
for table, rows in (("events", ev), ("deals", dl), ("places", pl)):
    for r in rows:
        if r.get("lat") is None:
            continue
        v = (r.get("venue") or r.get("name") or "").split(",")[-1].strip().lower()
        k = (round(r["lat"], 4), round(r["lng"], 4))
        pins[k].add(v)
        ref.setdefault(k, (table, r))
for k, vs in pins.items():
    if len(vs) >= 5:
        table, r = ref[k]
        add("PIN_SHARED", table, r, f"{k} x{len(vs)}: " + "; ".join(sorted(vs)[:6]))

# ---- POWTÓRKI (zasada właściciela 24.11.2026: to samo wydarzenie, oferta ani miejsce nie może być dwa razy) ----
VSTOP = set("the a an at by in of and for with hotel resort restaurant bar lounge cafe spa dubai abu dhabi sharjah ajman fujairah ras al khaimah umm quwain ain city centre center mall uae".split())
# słowa zbyt ogólne, żeby po nich rozpoznawać to samo (święta, rodzaje miejsc)
GEN = set("christmas eve day new year years brunch dinner lunch buffet night party festive live concert show museum park beach souk garden fort corniche club island pass happy hour ladies special edition 2026 2027".split())
# pary sprawdzone ręcznie jako RÓŻNE rzeczy (audit/not_dups.txt: 'idA idB' w linii) – nie zgłaszamy ich ponownie
try:
    NOT_DUP = {frozenset(l.split()[:2]) for l in open(os.path.join(os.path.dirname(__file__), "..", "audit", "not_dups.txt")) if len(l.split()) >= 2}
except OSError:
    NOT_DUP = set()
_add = add
def add(code, table, r, detail=""):
    if code.startswith("DUP_"):
        m = re.search(r"same as ([0-9a-f-]{36})", str(detail))
        if m and frozenset((r["id"], m.group(1))) in NOT_DUP:
            return
    _add(code, table, r, detail)
def toks(x):
    t = {w for w in re.findall(r"[a-z0-9]+", R.norm(x or "")) if len(w) > 2 and w not in VSTOP}
    return (t - GEN) or t
def nums(x):
    return set(re.findall(r"\d{2,5}", x or ""))
def same_venue(a, b):
    ta, tb = toks(a), toks(b)
    return bool(ta and tb and (ta <= tb or tb <= ta or len(ta & tb) >= max(2, min(len(ta), len(tb)) - 1)))
bycity = collections.defaultdict(list)
for r in dl:
    bycity[r.get("city")].append(r)
for c, rows in bycity.items():
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            va, vb = a.get("venue") or a.get("title"), b.get("venue") or b.get("title")
            if not same_venue(va, vb):
                continue
            da, dbb = set(a.get("days_of_week") or []), set(b.get("days_of_week") or [])
            days_ok = not da or not dbb or bool(da & dbb)
            same_type = a.get("deal_type") == b.get("deal_type")
            price_eq = bool(nums(a.get("price_text")) and nums(a.get("price_text")) == nums(b.get("price_text")))
            title_eq = toks(a.get("title")) and toks(b.get("title")) and len(toks(a["title"]) & toks(b["title"])) / min(len(toks(a["title"])), len(toks(b["title"]))) >= 0.6
            time_eq = bool(a.get("start_time")) and a.get("start_time") == b.get("start_time")
            if days_ok and ((same_type and (price_eq or title_eq)) or (price_eq and time_eq) or (title_eq and price_eq)):
                add("DUP_DEAL", "deals", b, f"same as {a['id']} '{(a.get('title') or '')[:40]}' @ {str(va)[:35]} | {a.get('deal_type')}/{b.get('deal_type')} | {(a.get('price_text') or '')[:30]} / {(b.get('price_text') or '')[:30]}")
pc = collections.defaultdict(list)
for r in pl:
    pc[r.get("city")].append(r)
for c, rows in pc.items():
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            ta, tb = toks(a["name"]), toks(b["name"])
            if not ta or not tb:
                continue
            near = a.get("lat") is not None and b.get("lat") is not None and km((a["lat"], a["lng"]), (b["lat"], b["lng"])) < 0.4
            share = len(ta & tb) / min(len(ta), len(tb))
            if ta == tb or (share >= 0.99 and min(len(ta), len(tb)) >= 2) or (near and share >= 0.5) or (share >= 0.67 and a.get("category") == b.get("category")):
                add("DUP_PLACE", "places", b, f"same as {a['id']} '{a['name'][:45]}' ({a.get('category')}/{b.get('category')}){' <400 m' if near else ''}")
ec = collections.defaultdict(list)
for r in ev:
    ec[(r.get("city"), r["start_date"])].append(r)
for k, rows in ec.items():
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            ta, tb = toks(a["title"]), toks(b["title"])
            if not ta or not tb:
                continue
            share = len(ta & tb) / min(len(ta), len(tb))
            st_ok = not a.get("start_time") or not b.get("start_time") or a["start_time"] == b["start_time"]
            if st_ok and (share >= 0.75 or (share >= 0.5 and same_venue(a.get("venue"), b.get("venue")) and min(len(ta), len(tb)) >= 2)):
                add("DUP_EVENT", "events", b, f"same as {a['id']} '{a['title'][:45]}' {a.get('start_time') or ''}/{b.get('start_time') or ''} @ {(a.get('venue') or '')[:30]} / {(b.get('venue') or '')[:30]}")

cnt = collections.Counter(o[0] for o in out)
print("SA|" + " ".join(f"{k}={v}" for k, v in sorted(cnt.items())))
for o in sorted(out):
    print("S|" + "|".join(str(x) for x in o))
