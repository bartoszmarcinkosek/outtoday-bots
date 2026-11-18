"""Wydarzenia z Eventbrite przez oficjalne API (token EVENTBRITE_TOKEN).

Eventbrite nie ma już publicznej wyszukiwarki w API, więc:
1. adresy wydarzeń w ZEA znajdujemy wyszukiwarką (web search w domenie eventbrite.com),
2. szczegóły każdego wydarzenia bierzemy z oficjalnego API (data, godzina, miejsce, cena),
3. organizatorów zapamiętujemy i co dzień pobieramy ich kolejne wydarzenia z API.

Nowe wpisy idą jako "pending" (do e-maila), bo na Eventbrite jest dużo B2B, wycieczek i ofert turystycznych.
Uruchamiane z workflow "Events bot" po głównym przebiegu. Bez tokenu nic nie robi.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from run import DB, titles_match  # noqa: E402

API = "https://www.eventbriteapi.com/v3"
SOURCE = "Eventbrite"
QUERIES = [
    "Dubai events December 2026", "Abu Dhabi events December 2026", "Sharjah events 2026", "Dubai workshop 2026",
    "Abu Dhabi workshop 2026", "Dubai comedy night", "Abu Dhabi comedy night", "Dubai live music 2026",
    "Abu Dhabi live music 2026", "Dubai kids activities 2026", "Dubai art class 2026", "Dubai run club race 2026",
    "Abu Dhabi community event 2026", "Dubai book club", "Dubai yoga event 2026", "Abu Dhabi language exchange",
    "Dubai pottery workshop", "Dubai salsa night", "Dubai quiz night", "Dubai market 2026",
]
# Wycieczki, pakiety podróży, B2B i targi branżowe nie są "powodem, żeby wyjść".
REJECT = re.compile(
    r"\b(b2b|summit|conference|forum|expo|exhibitors?|networking|investors?|startups?|pitch|masterclass for (business|founders)|"
    r"gitex|blockchain|crypto|trading|awards?|market trends|launch event|ai lab|predict|leadership|entrepreneurs?|"
    r"desert safari|safari|city tour|yacht tour|dhow cruise|travel|trip|getaway|takeover|experience 20\d\d|visa|job fair|"
    r"real estate|property|webinar|online)\b", re.I)
CAT = {"Music": "music", "Performing & Visual Arts": "culture", "Film, Media & Entertainment": "culture",
       "Food & Drink": "food", "Sports & Fitness": "sport", "Family & Education": "family", "Community & Culture": "community",
       "Charity & Causes": "community", "Hobbies & Special Interest": "classes", "Health & Wellness": "sport",
       "Travel & Outdoor": "nature", "Seasonal & Holiday": "festivals", "Nightlife": "nightlife", "Fashion & Beauty": "community"}
CITY = {"dubai": "Dubai", "abu dhabi": "Abu Dhabi", "al ain": "Al Ain", "sharjah": "Sharjah", "ajman": "Ajman",
        "ras al khaimah": "Ras Al Khaimah", "fujairah": "Fujairah", "umm al quwain": "Umm Al Quwain"}


def eb(token: str, path: str, **params) -> dict | None:
    r = requests.get(f"{API}{path}", headers={"Authorization": f"Bearer {token}"}, params=params, timeout=30)
    if r.status_code != 200:
        print(f"  API {path}: {r.status_code} {r.text[:120]}")
        return None
    return r.json()


def discover_ids(max_searches: int) -> set[str]:
    """Adresy eventbrite.com/e/... z wyszukiwarki (Claude web search ograniczony do eventbrite.com)."""
    import anthropic
    client = anthropic.Anthropic(max_retries=6)
    ids: set[str] = set()
    for q in QUERIES[:max_searches]:
        try:
            resp = client.messages.create(
                model=os.environ.get("BOT_MODEL", "claude-haiku-5-5"), max_tokens=600,
                tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 1,
                        "allowed_domains": ["eventbrite.com", "eventbrite.ae"]}],
                messages=[{"role": "user", "content": f"Search Eventbrite for: {q} (United Arab Emirates, upcoming). "
                                                      "Reply only with the event URLs you found, one per line."}])
        except Exception as e:  # noqa: BLE001
            print(f"  wyszukiwanie '{q}': {type(e).__name__}")
            continue
        text = " ".join(str(getattr(b, "text", "")) + str(getattr(b, "content", "")) for b in resp.content)
        ids |= set(re.findall(r"eventbrite\.(?:com|ae)/e/[^\s\"')]*?-(\d{9,})", text))
    return ids


def to_item(ev: dict, today: str) -> tuple[dict | None, str]:
    if ev.get("online_event") or ev.get("status") not in ("live", "started"):
        return None, f"online albo nieaktywne (status {ev.get('status')}, online {ev.get('online_event')}, start {(ev.get('start') or {}).get('local', '')[:10]})"
    v = ev.get("venue") or {}
    addr = v.get("address") or {}
    if (addr.get("country") or "").upper() != "AE":
        return None, "poza ZEA"
    title = (ev.get("name") or {}).get("text") or ""
    if REJECT.search(title):
        return None, "B2B / wycieczka / online"
    start, end = (ev.get("start") or {}).get("local"), (ev.get("end") or {}).get("local")
    if not start:
        return None, "brak daty"
    sd, st = start[:10], start[11:16]
    ed = end[:10] if end else None
    if (ed or sd) < today:
        return None, "minione"
    if ed and (dt.date.fromisoformat(ed) - dt.date.fromisoformat(sd)).days > 60:
        return None, "zbyt długi zakres (oferta stała, nie wydarzenie)"
    region = " ".join(filter(None, [addr.get("city"), addr.get("region"), addr.get("localized_address_display")])).lower()
    city = next((c for k, c in CITY.items() if k in region), None)
    if not city:
        return None, "nieznane emirat"
    venue = ", ".join(filter(None, [v.get("name"), addr.get("address_1")])) or None
    if not venue:
        return None, "brak miejsca"
    ta = ev.get("ticket_availability") or {}
    price, pmin, free = None, None, bool(ev.get("is_free"))
    mp = ta.get("minimum_ticket_price") or {}
    if free:
        price, pmin = "Free (registration on Eventbrite)", 0
    elif mp.get("major_value") and mp.get("currency"):
        val = float(mp["major_value"])
        price = f"From {mp['currency']} {val:g}" if mp["currency"] != "AED" else f"From AED {val:g}"
        pmin = round(val) if mp["currency"] == "AED" else None
    cat = CAT.get(((ev.get("category") or {}).get("name")) or "", "community")
    gaps = [g for g, ok in (("price", price is not None), ("start_time", st != "00:00")) if not ok]
    return {
        "title": title.strip(), "description": None, "category": cat, "start_date": sd, "end_date": ed if ed and ed != sd else None,
        "start_time": st if st != "00:00" else None, "end_time": (end or "")[11:16] or None if ed == sd else None,
        "venue": venue, "city": city, "price_text": price, "price_min_aed": pmin, "is_free": free,
        "url": ev.get("url"), "official_url": ev.get("url"), "source_name": SOURCE, "source_url": ev.get("url"),
        "status": "pending", "bot_key": f"eventbrite:{ev['id']}", "gaps": gaps,
        "evidence": {"page": ev.get("url"), "api": "Eventbrite API v3", "organizer_id": ev.get("organizer_id")},
    }, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--searches", type=int, default=len(QUERIES))
    args = ap.parse_args()
    token = os.environ.get("EVENTBRITE_TOKEN", "").strip()
    if not token:
        print("Brak EVENTBRITE_TOKEN: pomijam Eventbrite.")
        return 0
    me = eb(token, "/users/me/")
    print("Token:", "OK" if me else "NIE DZIAŁA")
    if not me:
        return 0
    db = DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=4))).date().isoformat()
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()

    found = discover_ids(args.searches)
    # Organizatorzy: z wyszukanych wydarzeń (nawet minionych) i zapamiętani wcześniej (bot_pages "eventbrite-org:<id>").
    # Ich bieżące wydarzenia bierzemy z API: wyszukiwarka często pokazuje stare strony, organizator ma nowe terminy.
    orgs = {r["url"].split(":", 1)[1] for r in db.get("bot_pages", {"select": "url", "url": "like.eventbrite-org:*", "limit": "2000"})}
    for i in sorted(found):
        ev = eb(token, f"/events/{i}/")
        if ev and ev.get("organizer_id"):
            orgs.add(str(ev["organizer_id"]))
    ids = set(found)
    for org in sorted(orgs)[:150]:
        data = eb(token, f"/organizers/{org}/events/", status="live", order_by="start_asc", page_size=50)
        evs = (data or {}).get("events", [])
        for e in evs:
            ids.add(str(e["id"]))
        if not args.dry_run:
            db.upsert("bot_pages", {"url": f"eventbrite-org:{org}", "last_fetched_at": now_iso,
                                    "last_status": f"Eventbrite organizer, live events: {len(evs)}"}, "url")
    print(f"Kandydaci: {len(ids)} (organizatorzy: {len(orgs)})")

    existing = db.get("events", {"select": "id,title,start_date,bot_key", "start_date": f"gte.{today}", "limit": "5000"})
    # Wszystkie wpisy z Eventbrite (także odrzucone i z przeszłą datą startu), żeby nie dodawać ich drugi raz.
    keys = {e.get("bot_key") for e in db.get("events", {"select": "bot_key", "bot_key": "like.eventbrite:*", "limit": "5000"})}
    added = skipped = 0
    for i in sorted(ids):
        if f"eventbrite:{i}" in keys:
            continue
        ev = eb(token, f"/events/{i}/", expand="venue,ticket_availability,category")
        if not ev:
            continue
        item, why = to_item(ev, today)
        if not item:
            skipped += 1
            print(f"  - {(ev.get('name') or {}).get('text', i)[:70]}: {why}")
            continue
        if any(e["start_date"] == item["start_date"] and titles_match(e["title"], item["title"]) for e in existing):
            print(f"  = {item['title'][:70]}: już jest")
            continue
        print(f"  + {item['title'][:70]} | {item['start_date']} {item['start_time'] or ''} | {item['venue'][:40]} | {item['price_text']}")
        if not args.dry_run:
            item["last_seen_at"] = now_iso
            db.insert("events", item)
        existing.append({"title": item["title"], "start_date": item["start_date"], "bot_key": item["bot_key"]})
        added += 1
    print(f"Eventbrite: nowe {added}, odrzucone {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
