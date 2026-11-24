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
AGG = tuple(getattr(R, "AGGREGATORS", ())) + ("timeoutdubai", "timeoutabudhabi", "cobone", "groupon", "yalla", "whatson.ae", "tripadvisor", "visitdubai.com/en/whats-on")

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

cnt = collections.Counter(o[0] for o in out)
print("SA|" + " ".join(f"{k}={v}" for k, v in sorted(cnt.items())))
for o in sorted(out):
    print("S|" + "|".join(str(x) for x in o))
