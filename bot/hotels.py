"""OutToday: oferty hoteli w całych ZEA (brunche, wieczory tematyczne, happy hours, ladies' nights,
day passy, śniadania, staycation).

Tryb 1 (--discover): AI szuka hoteli każdej sieci w każdym emiracie na OFICJALNYCH stronach sieci
          i zapisuje listę do sources/hotels.json (nazwa, emirat, strona hotelu).
Tryb 2 (--scan):     bot otwiera stronę hotelu i jego podstrony z ofertami/restauracjami (tylko ta sama domena),
          AI wypisuje oferty z dosłownymi cytatami, program sprawdza cytaty na stronie.
          Pewne (cena + dni, albo staycation z ceną) idą od razu do apki; reszta z ceną do porannego e-maila.
          Strony bez zmian od ostatniego razu są pomijane (taniej przy comiesięcznym przeglądzie).

Uruchomienie: python bot/hotels.py --discover
              python bot/hotels.py --scan --city "Ras Al Khaimah" --limit 40 [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402

HOTELS_FILE = os.path.join(os.path.dirname(__file__), "..", "sources", "hotels.json")
CITIES = ["Dubai", "Abu Dhabi", "Al Ain", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"]
TYPES = ["brunch", "dinner", "lunch", "breakfast", "happy_hour", "ladies_night", "night_out", "quiz", "day_pass", "staycation"]
DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

BRANDS = [
    ("Marriott, Sheraton, Westin, W, St. Regis, Ritz-Carlton, Le Méridien, JW Marriott, Courtyard, Four Points, Aloft, Element, Luxury Collection",
     ["marriott.com", "ritzcarlton.com"]),
    ("Hilton, Conrad, Waldorf Astoria, DoubleTree, Hilton Garden Inn, Hampton, Curio", ["hilton.com"]),
    ("InterContinental, Crowne Plaza, Holiday Inn, voco, Hotel Indigo, Staybridge", ["ihg.com", "icrasalkhaimah.com"]),
    ("Hyatt, Grand Hyatt, Park Hyatt, Andaz, Hyatt Regency, Hyatt Place", ["hyatt.com"]),
    ("Accor: Fairmont, Sofitel, Raffles, Swissôtel, Pullman, Novotel, Mercure, ibis, Mövenpick, Rixos, Banyan Tree",
     ["fairmont.com", "sofitel.accor.com", "raffles.com", "all.accor.com", "movenpick.com", "rixos.com", "pullman.accor.com",
      "novotel.accor.com", "swissotel.com", "banyantree.com"]),
    ("Rotana, Centro, Arjaan, Edge", ["rotana.com"]),
    ("Jumeirah", ["jumeirah.com"]),
    ("Radisson, Radisson Blu, Park Inn", ["radissonhotels.com"]),
    ("Rove", ["rovehotels.com"]),
    ("Anantara, Avani, NH, Tivoli", ["anantara.com", "avanihotels.com", "nh-hotels.com", "tivolihotels.com"]),
    ("Millennium, Copthorne", ["millenniumhotels.com"]),
    ("Kempinski, Shangri-La, Four Seasons, Mandarin Oriental, One&Only, Atlantis, Address, Vida, Palace Downtown",
     ["kempinski.com", "shangri-la.com", "fourseasons.com", "mandarinoriental.com", "oneandonlyresorts.com", "atlantis.com",
      "addresshotels.com", "vidahotels.com"]),
    ("Wyndham, Ramada, Days Inn, Melia, Habtoor, FIVE, SIRO, Taj, Hard Rock",
     ["wyndhamhotels.com", "melia.com", "habtoorhotels.com", "fivehotelsandresorts.com", "sirohotels.com", "tajhotels.com", "hardrockhotels.com"]),
]

HOTEL_LIST_TOOL = {
    "name": "report_hotels",
    "description": "Hotels found on the brand's official website.",
    "input_schema": {"type": "object", "properties": {"hotels": {"type": "array", "items": {"type": "object", "properties": {
        "name": {"type": "string"},
        "city": {"type": "string", "enum": CITIES},
        "url": {"type": "string", "description": "The hotel's own page on the official brand website (search result URL)."},
    }, "required": ["name", "city", "url"]}}}, "required": ["hotels"]},
}

OFFER_TOOL = {
    "name": "report_offers",
    "description": "Recurring public offers at this hotel's restaurants, bars, pools and rooms.",
    "input_schema": {"type": "object", "properties": {"offers": {"type": "array", "items": {"type": "object", "properties": {
        "title": {"type": "string", "description": "Offer name as on the page, e.g. 'Seafood Night', 'Saturday Brunch'"},
        "deal_type": {"type": "string", "enum": TYPES},
        "outlet": {"type": ["string", "null"], "description": "Restaurant/bar/pool name, if given"},
        "days": {"type": ["array", "null"], "items": {"type": "string", "enum": DAYS}},
        "start_time": {"type": ["string", "null"], "description": "HH:MM 24h"},
        "end_time": {"type": ["string", "null"], "description": "HH:MM 24h"},
        "price_text": {"type": ["string", "null"], "description": "All price tiers in AED as written, short (max 140 chars)"},
        "price_number": {"type": ["number", "null"], "description": "Lowest AED amount"},
        "valid_until": {"type": ["string", "null"], "description": "YYYY-MM-DD if the page states an end date"},
        "kid_friendly": {"type": "boolean"},
        "ladies_only": {"type": "boolean"},
        "details": {"type": "string", "description": "One short sentence in YOUR OWN words about what is included."},
        "evidence": {"type": "object", "description": "Exact verbatim snippets copied from PAGE TEXT.",
                     "properties": {k: {"type": ["string", "null"]} for k in ("offer", "price", "days", "time", "valid_until")},
                     "required": ["offer", "price", "days", "time", "valid_until"]},
    }, "required": ["title", "deal_type", "outlet", "days", "start_time", "end_time", "price_text", "price_number",
                    "valid_until", "kid_friendly", "ladies_only", "details", "evidence"]}}},
        "required": ["offers"]},
}
OFFER_RULES = """You read one UAE hotel web page. List only offers that the public can book:
- RECURRING offers: brunches, theme nights, buffets with drinks packages, happy hours, ladies' nights, quiz nights,
  business lunches, breakfast offers, pool/beach day passes;
- STAYCATION offers (room packages with a price per night), deal_type "staycation".
Skip: one-off holiday events (Christmas, New Year, Eid, Iftar, Valentine's), weddings, meetings, spa treatments, gift cards,
loyalty-member-only rates, offers that ended, anything without an AED price.
Use ONLY what PAGE TEXT says. Every price, day and time needs an exact verbatim quote in evidence. Null is better than a guess.
Never copy sentences into "details": write your own short sentence."""


def client_usage():
    import anthropic
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip()), {"input": 0, "output": 0, "calls": 0, "searches": 0}


def add_usage(usage: dict, resp) -> None:
    usage["input"] += resp.usage.input_tokens
    usage["output"] += resp.usage.output_tokens
    usage["calls"] += 1
    usage["searches"] += int(getattr(getattr(resp.usage, "server_tool_use", None), "web_search_requests", 0) or 0)


def cost(usage: dict) -> float:
    return usage["input"] / 1e6 * 0.10 + usage["output"] / 1e6 * 0.50 + usage["searches"] * 0.01


# ---------------------------------------------------------------- tryb 1: lista hoteli


def discover() -> int:
    client, usage = client_usage()
    try:
        hotels = json.load(open(HOTELS_FILE, encoding="utf-8"))
    except (OSError, ValueError):
        hotels = []
    known = {urlparse(h["url"]).netloc + urlparse(h["url"]).path.rstrip("/") for h in hotels}
    for brands, domains in BRANDS:
        for city in CITIES:
            prompt = (f"Search the official websites ({', '.join(domains)}) for ALL hotels and resorts of these brands in {city}, "
                      f"United Arab Emirates: {brands}. Report each hotel located in the emirate of {city} with its page URL "
                      "taken from the search results (the hotel's own page on the brand site). Skip hotels outside this emirate, "
                      "serviced apartments without restaurants and hotels not yet open. Call report_hotels (empty list if none).")
            try:
                resp = client.messages.create(
                    model=R.MODEL, max_tokens=4000,
                    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3, "allowed_domains": domains},
                           HOTEL_LIST_TOOL],
                    messages=[{"role": "user", "content": prompt}],
                )
            except Exception as e:
                print(f"[{brands[:20]} / {city}] błąd: {type(e).__name__}: {str(e)[:120]}")
                continue
            add_usage(usage, resp)
            found = []
            for b in resp.content:
                if getattr(b, "type", "") == "tool_use" and b.name == "report_hotels":
                    found = b.input.get("hotels") or []
            new = 0
            for h in found:
                u = str(h.get("url") or "")
                host = urlparse(u).netloc.lower()
                if not u.startswith("http") or not any(d in host for d in domains) or h.get("city") != city:
                    continue
                k = host + urlparse(u).path.rstrip("/")
                if k in known:
                    continue
                known.add(k)
                hotels.append({"name": h["name"].strip(), "city": city, "url": u})
                new += 1
            print(f"[{brands[:30]} / {city}] nowe hotele: {new}")
    # Hotele niezależne i lokalne sieci: zwykłe wyszukiwanie (bez portali), adres musi być stroną samego hotelu.
    blocked = ["booking.com", "expedia.com", "tripadvisor.com", "agoda.com", "hotels.com", "trip.com", "kayak.com",
               "trivago.com", "cobone.com", "groupon.ae", "whatson.ae", "timeoutdubai.com", "wow-rak.com", "visitdubai.com",
               "facebook.com", "instagram.com", "wikipedia.org", "makemytrip.com", "hotelscombined.com"]
    brand_domains = [d for _, ds in BRANDS for d in ds]
    for city in CITIES:
        for kind in ["beach resorts", "hotels with restaurants and bars", "4-star and 5-star hotels", "independent boutique hotels"]:
            prompt = (f"Find {kind} in the emirate of {city}, UAE, that are NOT part of these chains: {', '.join(b for b, _ in BRANDS)}. "
                      "For each, report the hotel's OWN official website URL (never a booking site, portal or review site). "
                      f"Only hotels located in {city}. Call report_hotels (empty list if none).")
            try:
                resp = client.messages.create(
                    model=R.MODEL, max_tokens=4000,
                    tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3, "blocked_domains": blocked},
                           HOTEL_LIST_TOOL],
                    messages=[{"role": "user", "content": prompt}],
                )
            except Exception as e:
                print(f"[niezależne / {city}] błąd: {type(e).__name__}")
                continue
            add_usage(usage, resp)
            new = 0
            for b in resp.content:
                if getattr(b, "type", "") == "tool_use" and b.name == "report_hotels":
                    for h in b.input.get("hotels") or []:
                        u = str(h.get("url") or "")
                        host = urlparse(u).netloc.lower()
                        if (not u.startswith("http") or h.get("city") != city or any(x in host for x in blocked)
                                or any(x in host for x in R.AGGREGATORS)):
                            continue
                        k = host + urlparse(u).path.rstrip("/")
                        if k in known:
                            continue
                        known.add(k)
                        hotels.append({"name": h["name"].strip(), "city": city, "url": u})
                        new += 1
            print(f"[niezależne {kind} / {city}] nowe hotele: {new}")
    hotels.sort(key=lambda h: (h["city"], h["name"]))
    with open(HOTELS_FILE, "w", encoding="utf-8") as f:
        json.dump(hotels, f, ensure_ascii=False, indent=1)
    print(f"\nHoteli na liście: {len(hotels)}. Koszt ok. ${cost(usage):.2f}")
    return 0


# ---------------------------------------------------------------- tryb 2: oferty


OFFER_LINK = re.compile(r"offer|dining|restaurant|bar|brunch|what.?s.?on|promotion|deal|experience|eat|drink|pool|beach|package", re.I)


def offer_pages(page: dict, base: str, limit: int = 4) -> list[str]:
    seen, out = set(), []
    host = urlparse(base).netloc
    for label, href in page.get("links") or []:
        if not href or not href.startswith("http") or urlparse(href).netloc != host:
            continue
        h = href.split("#")[0].rstrip("/")
        if h in seen or h == base.rstrip("/"):
            continue
        if OFFER_LINK.search(f"{label} {urlparse(h).path}") and not re.search(r"wedding|meeting|careers|gift|spa\b|room|suite|gallery|faq|login", h, re.I):
            seen.add(h)
            out.append(h)
    # najpierw strony z ofertami/brunchami
    out.sort(key=lambda u: 0 if re.search(r"offer|brunch|what.?s.?on|promotion|deal", u, re.I) else 1)
    return out[:limit]


def ask_offers(client, hotel: dict, text: str, url: str, usage: dict) -> list[dict]:
    msg = f"HOTEL: {hotel['name']} ({hotel['city']})\nPAGE URL: {url}\n\n=== PAGE TEXT ===\n{text[:R.MAX_TEXT]}\n=== END PAGE TEXT ==="
    for attempt in range(3):
        try:
            resp = client.messages.create(model=R.MODEL, max_tokens=4000, system=OFFER_RULES, tools=[OFFER_TOOL],
                                          tool_choice={"type": "tool", "name": "report_offers"},
                                          messages=[{"role": "user", "content": msg}])
            break
        except Exception as e:
            print(f"   [AI, próba {attempt + 1}] {type(e).__name__}")
            time.sleep(5 * (attempt + 1))
    else:
        return []
    add_usage(usage, resp)
    for b in resp.content:
        if b.type == "tool_use":
            offers = b.input.get("offers") or []
            for o in offers:
                if isinstance(o.get("evidence"), str):
                    try:
                        o["evidence"] = json.loads(o["evidence"])
                    except ValueError:
                        o["evidence"] = {}
            return [o for o in offers if isinstance(o, dict)]
    return []


ONE_OFF = re.compile(r"christmas|new year|nye|eid\b|iftar|suhoor|ramadan|valentine|easter|diwali|halloween|mother'?s day|father'?s day|national day", re.I)


def check_offer(o: dict, page_norm: str) -> tuple[dict | None, str]:
    ev = o.get("evidence") or {}
    if o.get("deal_type") not in TYPES:
        return None, "zły typ"
    if ONE_OFF.search(f"{o.get('title')} {ev.get('offer') or ''}"):
        return None, "jednorazowe (święto)"
    if not R.quote_on_page(ev.get("offer"), page_norm):
        return None, "brak cytatu oferty"
    pt, pq = (o.get("price_text") or "").strip(), ev.get("price")
    pn = o.get("price_number")
    if not (pt and len(pt) <= 160 and pn is not None and R.quote_on_page(pq, page_norm) and R.number_in_quote(pn, pq or "")
            and re.search(r"aed|dhs?|dirham", R.norm(f"{pt} {pq}"))):
        return None, "cena niepotwierdzona"
    vu = o.get("valid_until")
    if vu:
        try:
            if dt.date.fromisoformat(vu) < R.today_uae():
                return None, "oferta wygasła"
        except ValueError:
            vu = None
        if vu and not R.quote_on_page(ev.get("valid_until"), page_norm):
            vu = None
    out = {"title": o["title"].strip()[:120], "deal_type": o["deal_type"], "price_text": R.clean_price(pt),
           "details": (o.get("details") or "").strip()[:300] or None, "valid_until": vu,
           "kid_friendly": bool(o.get("kid_friendly")), "ladies_only": bool(o.get("ladies_only")) or o["deal_type"] == "ladies_night",
           "outlet": (o.get("outlet") or "").strip() or None}
    if o.get("days") and R.quote_on_page(ev.get("days"), page_norm):
        out["days_of_week"] = sorted({DAYS.index(d) for d in o["days"] if d in DAYS})
    tq = ev.get("time")
    st, et = R.parse_time(o.get("start_time")), R.parse_time(o.get("end_time"))
    if st and R.quote_on_page(tq, page_norm) and R.time_matches_quote(st, tq):
        out["start_time"] = st
        if et and R.time_matches_quote(et, tq):
            out["end_time"] = et
    if out["details"] and R.copied_text(out["details"], page_norm):
        out["details"] = None
    return out, ""


def venue_tokens(v: str) -> set[str]:
    stop = {"hotel", "resort", "the", "by", "at", "and", "&", "spa", "dubai", "abu", "dhabi", "sharjah", "ajman", "ras", "al",
            "khaimah", "fujairah", "umm", "quwain", "ain", "beach", "island", "restaurant", "bar"}
    return {t for t in R._tokens(v or "") if t not in stop}


def is_dup(row: dict, deals: list[dict]) -> bool:
    vt = venue_tokens(row["venue"])
    for d in deals:
        if d.get("city") != row["city"]:
            continue
        dt_ = venue_tokens(d.get("venue") or "")
        if vt and dt_ and len(vt & dt_) >= max(1, min(len(vt), len(dt_)) - 1):
            if R.titles_match(d.get("title") or "", row["title"]) or (
                    d.get("deal_type") == row["deal_type"] and d.get("days_of_week") == row.get("days_of_week")):
                return True
    return False


def scan(city: str | None, limit: int, dry: bool, force: bool) -> int:
    client, usage = client_usage()
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    hotels = json.load(open(HOTELS_FILE, encoding="utf-8"))
    if city:
        hotels = [h for h in hotels if h["city"] == city]
    deals = db.get("deals", {"select": "title,venue,city,deal_type,days_of_week,status", "limit": "10000"})
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    report, added, approved = [], 0, 0
    with R.Browser() as br:
        for hotel in hotels[:limit]:
            ok, why = R.robots_allows(hotel["url"])
            if not ok:
                report.append((hotel, "robots.txt", why))
                continue
            try:
                main = br.fetch(hotel["url"])
            except Exception as e:
                report.append((hotel, f"błąd {type(e).__name__}", ""))
                continue
            urls = [hotel["url"]] + offer_pages(main, main.get("final_url") or hotel["url"])
            hotel_new = 0
            for i, url in enumerate(urls):
                try:
                    page = main if i == 0 else br.fetch(url)
                except Exception:
                    continue
                if page.get("status", 200) >= 400 or len(page.get("text") or "") < 300:
                    continue
                text = page["text"]
                h = hashlib.sha1(R.norm(text).encode()).hexdigest()
                prev = db.get("bot_pages", {"select": "content_hash", "url": f"eq.{url}"})
                if prev and prev[0].get("content_hash") == h and not force:
                    continue
                page_norm = R.norm(text)
                for o in ask_offers(client, hotel, text, url, usage):
                    off, why = check_offer(o, page_norm)
                    if not off:
                        continue
                    venue = f"{off.pop('outlet')}, {hotel['name']}" if off.get("outlet") and R.norm(off["outlet"]) not in R.norm(hotel["name"]) else hotel["name"]
                    off.pop("outlet", None)
                    row = {**off, "venue": venue, "city": hotel["city"], "official_url": page.get("final_url") or url,
                           "source_name": "OutToday hotel bot (official site)"}
                    sure = bool(row.get("days_of_week")) or row["deal_type"] == "staycation"
                    row["status"] = "approved" if sure else "pending"
                    row = {k: v for k, v in row.items() if v not in (None, "", [])}
                    if is_dup(row, deals):
                        continue
                    if not dry:
                        db.insert("deals", row)
                    deals.append(row)
                    added += 1
                    approved += sure
                    hotel_new += 1
                    report.append((hotel, ("✓ " if sure else "? ") + f"{row['title']} — {row['price_text']}", row["official_url"]))
                if not dry:
                    db.upsert("bot_pages", {"url": url, "content_hash": h, "last_fetched_at": now_iso, "last_status": "hotels"}, "url")
                time.sleep(R.PAUSE_SECONDS)
            if not hotel_new:
                report.append((hotel, "brak nowych ofert z ceną", hotel["url"]))
    print("\n| Emirat | Hotel | Wynik | Strona |\n|---|---|---|---|")
    for h, res, u in report:
        print(f"| {h['city']} | {h['name']} | {res} | {u} |")
    print(f"\nHotele: {min(len(hotels), limit)}. Nowe oferty: {added} (od razu w apce: {approved}, do sprawdzenia: {added - approved}). "
          f"AI: {usage['calls']} wywołań, koszt ok. ${cost(usage):.2f}" + (" [próba – nic nie zapisano]" if dry else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--discover", action="store_true")
    ap.add_argument("--scan", action="store_true")
    ap.add_argument("--city", default="")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    if a.discover:
        return discover()
    if a.scan:
        return scan(a.city or None, a.limit, a.dry_run, a.force)
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
