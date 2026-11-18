"""OutToday: Cobone i Groupon tylko jako PODPOWIEDŹ.

1. Bot czyta listy ofert na Cobone/Groupon (robots.txt pozwala) i AI wypisuje: hotel/restauracja, miasto, rodzaj oferty.
2. Pomija hotele, które już mają taką ofertę w bazie.
3. Dla reszty szuka OFICJALNEJ strony hotelu (bez portali) i czyta z niej cenę, dni i godziny z cytatami.
4. Do bazy trafia tylko to, co potwierdza oficjalna strona. Cena z Cobone/Groupon NIGDY nie jest używana.

Uruchomienie: python bot/hints.py --limit 25 [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402
import verify as V  # noqa: E402

HINT_PAGES = [
    ("https://www.cobone.com/en/deals/food-dining-dubai", "Dubai"),
    ("https://www.cobone.com/en/deals/food-dining-dubai/filter/food-beverage/buffet", "Dubai"),
    ("https://www.cobone.com/en/deals/northern-emirates", None),
    ("https://www.cobone.com/en/deals/abu-dhabi", "Abu Dhabi"),
    ("https://www.groupon.ae/coupons/dubai/food-and-drink", "Dubai"),
    ("https://www.groupon.ae/coupons/abu-dhabi/food-and-drink", "Abu Dhabi"),
    ("https://www.groupon.ae/coupons/sharjah/food-and-drink", "Sharjah"),
]
CITIES = ["Dubai", "Abu Dhabi", "Al Ain", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain"]
TYPES = ["brunch", "dinner", "lunch", "happy_hour", "ladies_night", "day_pass", "breakfast", "quiz", "night_out"]

HINT_TOOL = {
    "name": "report_hints",
    "description": "List recurring hotel/restaurant dining or day-pass offers mentioned on this voucher page.",
    "input_schema": {
        "type": "object",
        "properties": {"hints": {"type": "array", "items": {"type": "object", "properties": {
            "venue": {"type": "string", "description": "Restaurant and/or hotel name, e.g. 'Horizon, Amwaj Rotana JBR'"},
            "city": {"type": "string", "enum": CITIES},
            "deal_type": {"type": "string", "enum": TYPES},
            "title": {"type": "string", "description": "Short name of the recurring offer, e.g. 'Seafood Night', 'Friday Brunch', 'Breakfast & Pool Access'"},
        }, "required": ["venue", "city", "deal_type", "title"]}}},
        "required": ["hints"],
    },
}
HINT_RULES = (
    "This is a voucher site or a city magazine/portal. Extract only RECURRING offers at hotels, restaurants, bars or beach clubs in the UAE: "
    "theme-night buffets, brunches, dinner or lunch buffets with unlimited drinks, happy hours, ladies' nights, "
    "breakfast with pool/beach access, pool/beach day passes. Skip spas, salons, cars, products, staycations (room nights), "
    "one-off holiday dinners (Christmas, New Year, Iftar), cinemas and anything outside the UAE. "
    "Never copy prices. At most 40 hints."
)


def extract_hints(client, text: str, default_city: str | None, usage: dict) -> list[dict]:
    msg = f"Default city if unclear: {default_city or 'unknown'}\n\n=== PAGE TEXT ===\n{text[:R.MAX_TEXT]}\n=== END ==="
    try:
        resp = client.messages.create(model=R.MODEL, max_tokens=3000, system=HINT_RULES, tools=[HINT_TOOL],
                                      tool_choice={"type": "tool", "name": "report_hints"},
                                      messages=[{"role": "user", "content": msg}])
    except Exception as e:
        print(f"   [AI] {type(e).__name__}")
        return []
    usage["input"] += resp.usage.input_tokens
    usage["output"] += resp.usage.output_tokens
    usage["calls"] += 1
    for b in resp.content:
        if b.type == "tool_use":
            return [h for h in (b.input.get("hints") or []) if isinstance(h, dict) and h.get("venue")]
    return []


PORTALS = ["yallaabudhabi.ae", "whatson.ae", "timeoutdubai.com", "timeoutabudhabi.com", "wow-rak.com"]
VOUCHERS = ["cobone.com", "groupon.ae"]
NOPRICE = {"happy_hour", "quiz", "ladies_night", "night_out"}
PORTAL_QUERIES = [
    (f"{kind} {city}", city)
    for city in ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain", "Al Ain"]
    for kind in ["happy hour bars pubs", "ladies night", "quiz night pub", "brunch", "theme night dinner unlimited drinks", "beach club day pass"]
]
SEARCH_QUERIES = [
    (f"{kind} {city}", city)
    for city in ["Dubai", "Abu Dhabi", "Sharjah", "Ajman", "Ras Al Khaimah", "Fujairah", "Umm Al Quwain", "Al Ain"]
    for kind in ["theme night dinner buffet unlimited beverages", "breakfast pool beach access", "brunch house beverages"]
]


def hints_from_search(client, query: str, city: str, usage: dict, domains: list[str] = VOUCHERS) -> list[dict]:
    prompt = (f"Search {', '.join(domains)} for: {query}. From the search results, list hotels, bars, pubs, clubs and restaurants "
              f"in {city} with a RECURRING offer (dining, happy hour, ladies' night, quiz, pool/beach access). " + HINT_RULES +
              " Then call report_hints with what you found (empty list if nothing).")
    try:
        resp = client.messages.create(
            model=R.MODEL, max_tokens=3000,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 2,
                    "allowed_domains": domains}, HINT_TOOL],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        print(f"   [AI] {type(e).__name__}: {str(e)[:120]}")
        return []
    usage["input"] += resp.usage.input_tokens
    usage["output"] += resp.usage.output_tokens
    usage["calls"] += 1
    usage["searches"] += int(getattr(getattr(resp.usage, "server_tool_use", None), "web_search_requests", 0) or 0)
    for b in resp.content:
        if getattr(b, "type", "") == "tool_use" and b.name == "report_hints":
            return [h for h in (b.input.get("hints") or []) if isinstance(h, dict) and h.get("venue") and h.get("city") == city]
    return []


def venue_key(v: str) -> str:
    stop = {"hotel", "resort", "the", "by", "at", "dubai", "abu", "dhabi", "sharjah", "ajman", "restaurant", "&", "and", "spa", "beach"}
    return " ".join(t for t in R._tokens(v) if t not in stop)


def known(h: dict, deals: list[dict]) -> bool:
    hk = set(venue_key(h["venue"]).split())
    for d in deals:
        if d.get("city") != h["city"]:
            continue
        dk = set(venue_key(d.get("venue") or "").split())
        if hk and dk and len(hk & dk) >= max(1, min(len(hk), len(dk)) // 2 + (1 if min(len(hk), len(dk)) > 2 else 0)):
            if d.get("deal_type") == h["deal_type"] or R.titles_match(d.get("title") or "", h["title"]):
                return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=25, help="ile nowych podpowiedzi sprawdzić na stronach oficjalnych")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip(), max_retries=6)
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    deals = db.get("deals", {"select": "title,venue,city,deal_type,status", "limit": "5000"})
    usage = {"input": 0, "output": 0, "calls": 0, "searches": 0}
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    added = 0
    report = []

    with R.Browser() as br:
        hints: list[dict] = []
        # Cobone i Groupon blokują boty (Cloudflare / 403), więc nie otwieramy ich stron.
        # Podpowiedzi bierzemy z wyników wyszukiwarki (fragmenty stron), a dane i tak tylko ze strony oficjalnej.
        for q, city in SEARCH_QUERIES:
            hs = hints_from_search(client, q, city, usage)
            print(f"[szukanie] {q}: {len(hs)} podpowiedzi")
            hints += hs
        # Portale (Yalla Abu Dhabi, What's On, Time Out, wow-rak): też tylko podpowiedzi z wyników wyszukiwarki.
        for q, city in PORTAL_QUERIES:
            hs = hints_from_search(client, q, city, usage, PORTALS)
            print(f"[portale] {q}: {len(hs)} podpowiedzi")
            hints += hs
        seen: set[str] = set()
        todo = []
        for h in hints:
            k = f"{h['city']}|{venue_key(h['venue'])}|{h['deal_type']}"
            if k in seen or known(h, deals):
                continue
            seen.add(k)
            todo.append(h)
        print(f"Nowe podpowiedzi (bez tych, które już mamy): {len(todo)}; sprawdzam {min(len(todo), args.limit)}")

        for h in todo[: args.limit]:
            row = {"title": h["title"], "venue": h["venue"], "city": h["city"]}
            url, why = V.find_official_url(client, "deals", row, usage)
            if not url:
                report.append((h, "brak strony oficjalnej", why))
                continue
            ok, rwhy = R.robots_allows(url)
            if not ok:
                report.append((h, "robots.txt", url))
                continue
            try:
                page = br.fetch(url)
            except Exception as e:
                report.append((h, f"błąd strony {type(e).__name__}", url))
                continue
            page_norm = R.norm(page["text"])
            raw = V.ask_facts(client, "deals", row, page["text"], url, usage)
            facts = V.check_facts(raw, page_norm, "deals", row)
            if not facts.get("found") or not (facts.get("price_text") or (h["deal_type"] in NOPRICE and facts.get("days"))):
                report.append((h, "strona nie potwierdza oferty z ceną", url))
                continue
            approved = bool(facts.get("days") or "daily" in R.norm(facts["evidence"].get("price") or ""))
            out = {
                "title": h["title"], "deal_type": h["deal_type"], "venue": h["venue"], "city": h["city"],
                "official_url": page.get("final_url") or url, "price_text": facts.get("price_text"),
                "days_of_week": facts.get("days"), "start_time": facts.get("start_time"), "end_time": facts.get("end_time"),
                "status": "approved" if approved else "pending",
                "source_name": "OutToday (official site; hint from voucher/portal site)",
            }
            out = {k: v for k, v in out.items() if v not in (None, [], "")}
            if not args.dry_run:
                db.insert("deals", out)
                deals.append(out)
            added += 1
            report.append((h, ("dodane" if approved else "dodane do sprawdzenia") + f": {facts.get('price_text') or 'bez ceny'}", url))
            time.sleep(R.PAUSE_SECONDS)

    print("\n| Miasto | Miejsce | Oferta | Wynik | Strona |\n|---|---|---|---|---|")
    for h, res, u in report:
        print(f"| {h['city']} | {h['venue']} | {h['title']} | {res} | {u} |")
    cost = usage["input"] / 1e6 * 0.10 + usage["output"] / 1e6 * 0.50 + usage["searches"] * 0.01
    print(f"\nDodane: {added}. Wywołania AI: {usage['calls']}, wyszukiwania: {usage['searches']}, koszt ok. ${cost:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
