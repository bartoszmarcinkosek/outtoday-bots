"""OutToday: sprawdzanie miejsc i promocji (ceny, godziny, dni) na stronach oficjalnych.

Krok A (tylko z --find-urls): dla wpisów bez oficjalnej strony AI szuka jej w internecie
         (bez portali). Znaleziony link trafia do e-maila jako propozycja, nic nie jest wpisywane samo.
Krok B: bot otwiera stronę oficjalną, AI wypisuje cenę / godziny / dni z dosłownymi cytatami,
         program sprawdza cytaty na stronie i porównuje z bazą. Różnice idą do bot_changes
         (sekcja "Zmiany" w porannym e-mailu). Nic nie jest nadpisywane.

Uruchomienie: python bot/verify.py --table deals --limit 20 --dry-run
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

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402  (wspólne narzędzia: przeglądarka, robots.txt, sprawdzanie cytatów)

DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]  # 0 = niedziela, jak w bazie
SEARCH_BLOCKED = [
    "platinumlist.net", "feverup.com", "yallaabudhabi.ae", "whatson.ae", "timeoutdubai.com", "timeoutabudhabi.com",
    "tripadvisor.com", "booking.com", "expedia.com", "agoda.com", "groupon.ae", "cobone.com", "zomato.com",
    "talabat.com", "deliveroo.ae", "facebook.com", "instagram.com", "tiktok.com", "wow-rak.com", "koobit.com",
    "dubaifaqs.com", "propertyfinder.ae", "bayut.com", "magpie.ae", "edarabia.com", "theentertainerme.com",
]

FACT_TOOL = {
    "name": "report_facts",
    "description": "Report what this page says about the one item.",
    "input_schema": {
        "type": "object",
        "properties": {
            "found": {"type": "boolean", "description": "True only if the page clearly describes THIS item (same offer at the same venue)."},
            "price_text": {"type": ["string", "null"], "description": "Price with its conditions, as written (e.g. 'AED 150 per adult, includes AED 100 F&B credit'). Null if not on the page."},
            "price_number": {"type": ["number", "null"], "description": "Lowest AED amount from price_text."},
            "hours_text": {"type": ["string", "null"], "description": "Opening hours / session times as written. Null if not on the page."},
            "days": {"type": ["array", "null"], "items": {"type": "string", "enum": DAYS}, "description": "Days of the week the offer runs, only if the page says so."},
            "start_time": {"type": ["string", "null"], "description": "HH:MM 24h start of the offer, if written."},
            "end_time": {"type": ["string", "null"], "description": "HH:MM 24h end of the offer, if written."},
            "phone": {"type": ["string", "null"], "description": "Phone number for this venue as written on the page."},
            "evidence": {
                "type": "object",
                "description": "Exact verbatim snippets copied from PAGE TEXT for each non-null field.",
                "properties": {k: {"type": ["string", "null"]} for k in ("item", "price", "hours", "days", "time", "phone")},
                "required": ["item", "price", "hours", "days", "time", "phone"],
            },
        },
        "required": ["found", "price_text", "price_number", "hours_text", "days", "start_time", "end_time", "phone", "evidence"],
    },
}

FACT_RULES = """You check one listing for OutToday against its official web page.
Use ONLY what PAGE TEXT says. Never guess. Null is better than a guess.
Every non-null field needs an exact verbatim quote from PAGE TEXT in evidence.
If the page does not clearly describe this exact item (same offer, same venue), set found=false and everything else null.
Prices: AED amounts with their conditions (per person, per adult, includes credit, weekday/weekend). If weekday and weekend prices differ, keep both in price_text.
"""


def item_label(table: str, row: dict) -> str:
    if table == "places":
        return f"{row['name']} ({row.get('category') or ''}, {row.get('area') or ''} {row.get('city') or ''})"
    return f"{row['title']} at {row.get('venue') or '?'} ({row.get('city') or ''})"


# ---------------------------------------------------------------- krok A: szukanie strony oficjalnej


def find_official_url(client, table: str, row: dict, usage: dict) -> tuple[str | None, str]:
    what = item_label(table, row)
    prompt = (
        f"Find the OFFICIAL web page for this UAE listing: {what}.\n"
        "Official means the venue's, hotel's, restaurant's or operator's own website (including the hotel brand site, "
        "e.g. marriott.com, hilton.com, jumeirah.com), ideally the exact page for this offer or venue.\n"
        "Never return listing portals, review sites, ticket resellers, social media or news articles.\n"
        "If you cannot find an official page with confidence, return none.\n"
        "Answer with ONE line of JSON only: {\"url\": \"https://...\" or null, \"why\": \"short reason\"}"
    )
    try:
        resp = client.messages.create(
            model=R.MODEL,
            max_tokens=1500,
            tools=[{"type": "web_search_20250305", "name": "web_search", "max_uses": 3,
                    "blocked_domains": SEARCH_BLOCKED,
                    "user_location": {"type": "approximate", "country": "AE", "timezone": "Asia/Dubai"}}],
            messages=[{"role": "user", "content": prompt}],
        )
    except Exception as e:
        return None, f"błąd wyszukiwania: {type(e).__name__}"
    usage["input"] += resp.usage.input_tokens
    usage["output"] += resp.usage.output_tokens
    usage["calls"] += 1
    usage["searches"] = usage.get("searches", 0) + int(getattr(getattr(resp.usage, "server_tool_use", None), "web_search_requests", 0) or 0)
    text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
    m = re.search(r"\{[^{}]*\"url\"[^{}]*\}", text)
    if not m:
        return None, "brak odpowiedzi"
    try:
        data = json.loads(m.group(0))
    except ValueError:
        return None, "zła odpowiedź"
    url = data.get("url")
    if not url or not str(url).startswith("http"):
        return None, data.get("why") or "nie znaleziono"
    host = R.urlparse(url).netloc.lower()
    if any(b in host for b in SEARCH_BLOCKED) or any(a in host for a in R.AGGREGATORS):
        return None, f"odrzucony portal: {host}"
    return url, data.get("why") or ""


# ---------------------------------------------------------------- krok B: sprawdzenie na stronie


def check_facts(raw: dict, page_norm: str) -> dict:
    """Zostawia tylko pola potwierdzone cytatem ze strony."""
    ev = raw.get("evidence") or {}
    out: dict = {"evidence": {}}
    if not raw.get("found") or not R.quote_on_page(ev.get("item"), page_norm):
        return {"found": False}
    out["found"] = True
    pq = ev.get("price")
    if raw.get("price_text") and R.quote_on_page(pq, page_norm) and (
        raw.get("price_number") is None or R.number_in_quote(raw["price_number"], pq)
    ):
        out["price_text"] = R.clean_price(raw["price_text"])
        out["price_number"] = raw.get("price_number")
        out["evidence"]["price"] = pq
    hq = ev.get("hours")
    if raw.get("hours_text") and R.quote_on_page(hq, page_norm):
        out["hours_text"] = raw["hours_text"].strip()
        out["evidence"]["hours"] = hq
    dq = ev.get("days")
    if raw.get("days") and R.quote_on_page(dq, page_norm):
        out["days"] = sorted({DAYS.index(d) for d in raw["days"] if d in DAYS})
        out["evidence"]["days"] = dq
    tq = ev.get("time")
    st, et = R.parse_time(raw.get("start_time")), R.parse_time(raw.get("end_time"))
    if st and R.quote_on_page(tq, page_norm) and R.time_matches_quote(st, tq):
        out["start_time"] = st
        out["end_time"] = et if et and R.time_matches_quote(et, tq) else None
        out["evidence"]["time"] = tq
    phq = ev.get("phone")
    if raw.get("phone") and R.quote_on_page(phq, page_norm):
        digits = re.sub(r"\D", "", raw["phone"])
        if len(digits) >= 7 and digits[-7:] in re.sub(r"\D", "", phq):
            out["phone"] = raw["phone"].strip()
            out["evidence"]["phone"] = phq
    return out


def first_number(s: str | None) -> float | None:
    m = re.search(r"\d+(?:\.\d+)?", (s or "").replace(",", ""))
    return float(m.group(0)) if m else None


def diffs_for(table: str, row: dict, facts: dict) -> list[tuple[str, str | None, str, str | None]]:
    """(pole, stara wartość, nowa wartość, cytat). Tylko prawdziwe różnice."""
    out = []
    if "price_text" in facts:
        old, new = row.get("price_text"), facts["price_text"]
        on, nn = first_number(old), facts.get("price_number") or first_number(new)
        if not old or (on is not None and nn is not None and abs(on - nn) > 0.01):
            out.append(("price_text", old, new, facts["evidence"]["price"]))
    if table == "places" and "hours_text" in facts:
        old = row.get("hours_text")
        if not old or R.norm(re.sub(r"\s", "", old)) != R.norm(re.sub(r"\s", "", facts["hours_text"])):
            if not old or set(re.findall(r"\d+", old)) != set(re.findall(r"\d+", facts["hours_text"])):
                out.append(("hours_text", old, facts["hours_text"], facts["evidence"]["hours"]))
    if table == "deals":
        if "days" in facts and facts["days"]:
            old = sorted(row.get("days_of_week") or [])
            if old != facts["days"]:
                fmt = lambda xs: ",".join(DAYS[i] for i in xs) if xs else None
                out.append(("days_of_week", fmt(old), fmt(facts["days"]), facts["evidence"]["days"]))
        if facts.get("start_time"):
            old = (row.get("start_time") or "")[:5] or None
            if old != facts["start_time"]:
                out.append(("start_time", old, facts["start_time"], facts["evidence"]["time"]))
        if facts.get("end_time"):
            old = (row.get("end_time") or "")[:5] or None
            if old != facts["end_time"]:
                out.append(("end_time", old, facts["end_time"], facts["evidence"]["time"]))
    if facts.get("phone") and not row.get("phone"):
        out.append(("phone", None, facts["phone"], facts["evidence"]["phone"]))
    return out


def ask_facts(client, table: str, row: dict, text: str, url: str, usage: dict) -> dict:
    msg = (f"ITEM: {item_label(table, row)}\n"
           f"Currently listed as: price={row.get('price_text')!r}"
           + (f", hours={row.get('hours_text')!r}" if table == "places" else
              f", days={[DAYS[i] for i in (row.get('days_of_week') or []) if 0 <= i < 7]}, time={row.get('start_time')}-{row.get('end_time')}, details={row.get('details')!r}")
           + f"\nPAGE URL: {url}\n\n=== PAGE TEXT ===\n{text[:R.MAX_TEXT]}\n=== END PAGE TEXT ===")
    for attempt in range(3):
        try:
            resp = client.messages.create(
                model=R.MODEL, max_tokens=2000, system=FACT_RULES, tools=[FACT_TOOL],
                tool_choice={"type": "tool", "name": "report_facts"},
                messages=[{"role": "user", "content": msg}],
            )
            break
        except Exception as e:
            print(f"   [AI błąd, próba {attempt + 1}] {type(e).__name__}")
            time.sleep(5 * (attempt + 1))
    else:
        return {}
    usage["input"] += resp.usage.input_tokens
    usage["output"] += resp.usage.output_tokens
    usage["calls"] += 1
    for b in resp.content:
        if b.type == "tool_use":
            data = b.input
            if isinstance(data.get("evidence"), str):
                try:
                    data["evidence"] = json.loads(data["evidence"])
                except ValueError:
                    data["evidence"] = {}
            return data
    return {}


# ---------------------------------------------------------------- główna pętla


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", choices=["places", "deals", "all"], default="all")
    ap.add_argument("--limit", type=int, default=400)
    ap.add_argument("--find-urls", action="store_true", help="szukaj stron oficjalnych dla wpisów bez linku (płatne wyszukiwanie, ok. 1 grosz za wyszukanie)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true", help="sprawdź nawet strony bez zmian")
    args = ap.parse_args()

    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    usage = {"input": 0, "output": 0, "calls": 0, "searches": 0}
    report: list[dict] = []
    tables = ["deals", "places"] if args.table == "all" else [args.table]

    open_changes = db.get("bot_changes", {"select": "table_name,row_id,field,new_value", "handled": "eq.false", "limit": "5000"})
    already = {(c["table_name"], c["row_id"], c["field"], c["new_value"]) for c in open_changes}

    done = 0
    with R.Browser() as br:
        R._BROWSER = br
        for table in tables:
            cols = ("id,name,category,area,city,hours_text,price_text,is_free,url,official_url,phone,status" if table == "places"
                    else "id,title,venue,area,city,details,days_of_week,start_time,end_time,price_text,url,official_url,phone,deal_type,status")
            rows = db.get(table, {"select": cols, "status": "in.(approved,pending)", "order": "updated_at.asc.nullsfirst", "limit": "2000"})
            if table == "places":
                rows = [r for r in rows if not r.get("is_free") or not r.get("hours_text")]  # darmowe z godzinami: nic do sprawdzania
            for row in rows:
                if done >= args.limit:
                    break
                label = row.get("name") or row.get("title")
                url = row.get("official_url")
                rep = {"table": table, "item": label, "url": url or "", "result": ""}
                report.append(rep)

                if not url:
                    if not args.find_urls:
                        rep["result"] = "brak strony oficjalnej (uruchom z --find-urls)"
                        continue
                    done += 1
                    url, why = find_official_url(client, table, row, usage)
                    if not url:
                        rep["result"] = f"nie znaleziono strony: {why}"
                        continue
                    rep["url"] = url
                    rep["result"] = "propozycja strony; "
                    key = (table, row["id"], "official_url", url)
                    if not args.dry_run and key not in already:
                        db.insert("bot_changes", {"table_name": table, "row_id": row["id"], "field": "official_url",
                                                  "old_value": None, "new_value": url, "evidence": why[:300], "source_url": url})
                        already.add(key)
                else:
                    done += 1

                ok, why = R.robots_allows(url)
                if not ok:
                    rep["result"] += why
                    continue
                try:
                    page = br.fetch(url)
                except Exception as e:
                    rep["result"] += f"błąd pobierania: {type(e).__name__}"
                    continue
                text = page["text"] or ""
                if page["status"] >= 400 or len(text) < 200:
                    rep["result"] += f"strona nie działa (HTTP {page['status']})"
                    if not args.dry_run and row.get("official_url") and page["status"] in (404, 410):
                        key = (table, row["id"], "official_url", "")
                        if key not in already:
                            db.insert("bot_changes", {"table_name": table, "row_id": row["id"], "field": "official_url",
                                                      "old_value": url, "new_value": "", "evidence": f"Strona zwraca błąd {page['status']}", "source_url": url})
                            already.add(key)
                    continue

                h = hashlib.sha256((R.norm(text) + json.dumps(row, sort_keys=True, default=str)).encode()).hexdigest()
                page_key = f"{table}:{row['id']}"
                if not args.force:
                    prev = db.get("bot_pages", {"select": "content_hash", "url": f"eq.{page_key}"})
                    if prev and prev[0]["content_hash"] == h:
                        rep["result"] += "bez zmian od ostatniego sprawdzenia"
                        continue

                raw = ask_facts(client, table, row, text, page["final_url"], usage)
                facts = check_facts(raw, R.norm(text))
                if not facts.get("found"):
                    rep["result"] += "strona nie opisuje tej pozycji (sprawdź ręcznie)"
                else:
                    diffs = diffs_for(table, row, facts)
                    rep["result"] += ("ZMIANY: " + "; ".join(f"{f}: {o} -> {n}" for f, o, n, _ in diffs)) if diffs else "zgodne ze stroną"
                    if not args.dry_run:
                        for f, o, n, q in diffs:
                            key = (table, row["id"], f, n)
                            if key in already:
                                continue
                            db.insert("bot_changes", {"table_name": table, "row_id": row["id"], "field": f,
                                                      "old_value": None if o is None else str(o), "new_value": str(n),
                                                      "evidence": q, "source_url": page["final_url"]})
                            already.add(key)
                if not args.dry_run:
                    db.upsert("bot_pages", {"url": page_key, "content_hash": h, "last_fetched_at": now_iso, "last_status": rep["result"][:200]}, "url")
                time.sleep(R.PAUSE_SECONDS)

    # raport
    lines = [f"# OutToday: sprawdzanie miejsc i promocji {'(PRÓBA)' if args.dry_run else ''}", "",
             f"Wywołania AI: {usage['calls']}, wyszukiwania: {usage['searches']}, tokeny: {usage['input']} / {usage['output']}", "",
             "| Tabela | Pozycja | Wynik |", "|---|---|---|"]
    for r in report:
        if r["result"]:
            lines.append(f"| {r['table']} | {str(r['item'])[:60].replace('|', '/')} | {r['result'][:160].replace('|', '/')} |")
    md = "\n".join(lines) + "\n"
    print(md)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(md)
    if not args.dry_run:
        db.insert("bot_runs", {"dry_run": False, "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                               "summary": {"kind": "verify", "usage": usage, "checked": done}})
    return 0


if __name__ == "__main__":
    sys.exit(main())
