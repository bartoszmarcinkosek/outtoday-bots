"""Tylko odczyt: test filtrów apki (Free, Kids, Ladies only, Indoor) na prawdziwych danych.
Pomysł właściciela 26.11.2026 po zgłoszeniu testera (Free pokazywał płatne, Ladies only był pusty).
Linie: FX|filtr|tabela|id|miasto|tytuł|powód|cena|link ; FZ| podsumowanie. Logika filtrów jak w app/src/logic.ts."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
t = R.today_uae().isoformat()

LADIES_RE = re.compile(r"\b(ladies|women|woman|girls)[' ]*(only|night|day|evening|morning)\b|\bfor (ladies|women)\b|\bwomen'?s (only|session|class|swim)|\bladies'? beach\b|\bsisterhood\b", re.I)
AED = re.compile(r"AED\s*([\d,]+(?:\.\d+)?)", re.I)


def parse_price(text):  # jak parsePrice w logic.ts
    if not text:
        return None
    m = AED.search(text)
    if re.match(r"^\s*free\b", text, re.I) and not m and not re.match(r"^\s*free\s+(for|with|before|until|till|on|if|to|after|when)\b", text, re.I):
        return 0
    return float(m.group(1).replace(",", "")) if m else None


PAID = re.compile(r"(?<!vendor )(?<!stall )(?<!table )\b(tickets? (from|start|cost|priced)|entry (fee|costs?)|admission (fee|costs?|is aed)|from aed\s*[1-9]|aed\s*[1-9]\d* (per|pp|/)|court fee|class fee|per person|per child)\b", re.I)
ADULT = re.compile(r"\b(18\+|21\+|adults? only|over 18|over 21|ladies'? night|happy hour|pub crawl|nightclub|wine (tasting|pairing)|beer|cocktail|bar crawl|casino|burlesque)\b", re.I)
KIDS = re.compile(r"\b(kids?|children|child|toddlers?|famil(y|ies)|junior|teens?|little ones)\b", re.I)
MEN = re.compile(r"\b(men only|gentlemen only|for men)\b", re.I)

out, n = [], {}


def flag(f, tbl, x, why, title, price=""):
    n[f] = n.get(f, 0) + 1
    out.append(f"FX|{f}|{tbl}|{x['id']}|{x.get('city')}|{title}|{why}|{price or ''}|{x.get('official_url') or ''}")


ev = db.get("events", {"select": "id,city,title,description,category,price_text,price_min_aed,is_free,kid_friendly,ladies_only,official_url,source_name",
                       "status": "eq.approved", "or": f"(end_date.gte.{t},and(end_date.is.null,start_date.gte.{t}))", "limit": "3000"})
pl = db.get("places", {"select": "id,city,name,description,category,price_text,is_free,kid_friendly,ladies_only,is_indoor,official_url", "status": "eq.approved", "limit": "3000"})
dl = db.get("deals", {"select": "id,city,title,details,deal_type,price_text,kid_friendly,ladies_only,official_url", "status": "eq.approved", "limit": "3000"})

for e in ev:
    txt = f"{e['title']} {e.get('description') or ''}"
    pr = 0 if e.get("is_free") else (e.get("price_min_aed") if e.get("price_min_aed") is not None else parse_price(e.get("price_text")))
    free = bool(e.get("is_free")) or pr == 0
    if free:
        if "meetup" in (e.get("source_name") or "").lower():
            flag("free", "events", e, "Meetup: darmowy tylko zapis", e["title"], e.get("price_text"))
        elif (e.get("price_min_aed") or 0) > 0 or (AED.search(e.get("price_text") or "") and float(AED.search(e["price_text"]).group(1).replace(",", "") or 0) > 0):
            flag("free", "events", e, "is_free, a cena w AED", e["title"], e.get("price_text"))
        elif PAID.search(txt):
            flag("free", "events", e, f"opis mówi o opłacie: '{PAID.search(txt).group(0)}'", e["title"], e.get("price_text"))
    elif re.match(r"^\s*(free|free entry|free admission|complimentary)\s*$", e.get("price_text") or "", re.I):
        flag("free", "events", e, "cena 'Free', ale nie w filtrze Free", e["title"], e.get("price_text"))
    if e.get("kid_friendly") and ADULT.search(txt):
        flag("kids", "events", e, f"w filtrze Kids, a tekst: '{ADULT.search(txt).group(0)}'", e["title"])
    elif not e.get("kid_friendly") and (e.get("category") == "family" or KIDS.search(e["title"])) and not ADULT.search(txt):
        flag("kids", "events", e, "rodzinne/dla dzieci, a poza filtrem Kids", e["title"])
    lad = bool(e.get("ladies_only")) or bool(LADIES_RE.search(txt))
    if lad and MEN.search(txt):
        flag("ladies", "events", e, "w Ladies only, a tekst mówi o mężczyznach", e["title"])

for p in pl:
    txt = f"{p['name']} {p.get('description') or ''}"
    cat = p.get("category") or ""
    indoor = p.get("is_indoor") if p.get("is_indoor") is not None else (False if cat in ("beaches", "parks", "daytrips") else True if cat in ("museums", "markets", "studios") else None)
    if p.get("is_indoor") is None and indoor is True and cat in ("beaches", "parks", "daytrips"):
        flag("indoor", "places", p, f"Indoor, a kategoria {cat}", p["name"])
    if indoor is True and re.search(r"\b(beach|outdoor|open[- ]air|desert|dunes?|wadi|hike|trail|safari)\b", p["name"], re.I):
        flag("indoor", "places", p, "Indoor, a nazwa wskazuje na zewnątrz", p["name"])
    free = bool(p.get("is_free")) or parse_price(p.get("price_text")) == 0
    if free and (AED.search(p.get("price_text") or "") and float(AED.search(p["price_text"]).group(1).replace(",", "")) > 0):
        flag("free", "places", p, "is_free, a cena w AED", p["name"], p.get("price_text"))
    if p.get("kid_friendly") and ADULT.search(txt):
        flag("kids", "places", p, f"w filtrze Kids, a tekst: '{ADULT.search(txt).group(0)}'", p["name"])

for d in dl:
    txt = f"{d['title']} {d.get('details') or ''}"
    if parse_price(d.get("price_text")) == 0 and not re.search(r"\bfree\b", d.get("price_text") or "", re.I):
        flag("free", "deals", d, "oferta w Free bez słowa free", d["title"], d.get("price_text"))
    if d.get("kid_friendly") and (ADULT.search(txt) or d.get("deal_type") in ("ladies_night", "happy_hour")):
        flag("kids", "deals", d, f"w filtrze Kids, a to {d.get('deal_type')}", d["title"])

print(f"FZ|events {len(ev)} places {len(pl)} deals {len(dl)}|" + " ".join(f"{k}={v}" for k, v in sorted(n.items())))
print("\n".join(out))
