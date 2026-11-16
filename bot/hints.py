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
    "This is a voucher site. Extract only RECURRING offers at hotels, restaurants, bars or beach clubs in the UAE: "
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
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    deals = db.get("deals", {"select": "title,venue,city,deal_type,status", "limit": "5000"})
    usage = {"input": 0, "output": 0, "calls": 0, "searches": 0}
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    added = 0
    report = []

    with R.Browser() as br:
        hints: list[dict] = []
        for url, city in HINT_PAGES:
            ok, why = R.robots_allows(url)
            if not ok:
                print(f"robots.txt nie pozwala: {url} ({why})")
                continue
            try:
                page = br.fetch(url)
            except Exception as e:
                print(f"błąd {url}: {e}")
                continue
            hs = extract_hints(client, page["text"], city, usage)
            print(f"{url}: status {page.get('status')}, tekst {len(page['text'])} znaków, {len(hs)} podpowiedzi")
            if not hs:
                print("   początek strony:", re.sub(r"\s+", " ", page["text"][:300]))
            hints += hs
            time.sleep(R.PAUSE_SECONDS)

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
            if not facts.get("found") or not facts.get("price_text"):
                report.append((h, "strona nie potwierdza oferty z ceną", url))
                continue
            approved = bool(facts.get("days") or "daily" in R.norm(facts["evidence"].get("price") or ""))
            out = {
                "title": h["title"], "deal_type": h["deal_type"], "venue": h["venue"], "city": h["city"],
                "official_url": page.get("final_url") or url, "price_text": facts["price_text"],
                "days_of_week": facts.get("days"), "start_time": facts.get("start_time"), "end_time": facts.get("end_time"),
                "status": "approved" if approved else "pending",
                "source_name": "OutToday (official site; hint from voucher site)",
            }
            out = {k: v for k, v in out.items() if v not in (None, [], "")}
            if not args.dry_run:
                db.insert("deals", out)
                deals.append(out)
            added += 1
            report.append((h, ("dodane" if approved else "dodane do sprawdzenia") + f": {facts['price_text']}", url))
            time.sleep(R.PAUSE_SECONDS)

    print("\n| Miasto | Miejsce | Oferta | Wynik | Strona |\n|---|---|---|---|---|")
    for h, res, u in report:
        print(f"| {h['city']} | {h['venue']} | {h['title']} | {res} | {u} |")
    cost = usage["input"] / 1e6 * 0.10 + usage["output"] / 1e6 * 0.50 + usage["searches"] * 0.01
    print(f"\nDodane: {added}. Wywołania AI: {usage['calls']}, wyszukiwania: {usage['searches']}, koszt ok. ${cost:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
