"""OutToday: eventy z postów na Instagramie oficjalnych kont (hotele, areny, muzea, organizatorzy).

1. Czyta najnowsze posty kont z sources/instagram.json przez oficjalne Instagram Graph API (business_discovery).
2. Pomija posty już przeczytane (tabela bot_pages) i starsze niż 30 dni.
3. AI (Haiku) wypisuje eventy WYŁĄCZNIE z opisu posta, z dosłownymi cytatami; program sprawdza każdy cytat.
4. Każdy event z Instagrama trafia jako 'pending' (do zatwierdzenia w porannym mailu). Bez daty = pomijany.

Uruchomienie: python bot/instagram.py [--limit 80] [--dry-run]
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

import requests

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402
import hotels as H  # noqa: E402

G = "https://graph.facebook.com/v21.0"
MAX_AGE_DAYS = 30
POSTS_PER_ACCOUNT = 12
HINT = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b|\b\d{1,2}(st|nd|rd|th)\b|\b\d{1,2}[./]\d{1,2}\b|"
                  r"\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*day\b|tonight|this weekend|aed|tickets?|book now|\bpm\b", re.I)


OFFER_HINT = re.compile(r"brunch|happy hour|ladies|business lunch|set menu|breakfast|day pass|pool pass|beach pass|staycation|"
                        r"quiz|unlimited|free.?flow|\bdeal\b|offer|aed|dhs", re.I)


def ig_user_id(tok: str) -> str:
    r = requests.get(f"{G}/me/accounts", params={"fields": "instagram_business_account{id}", "access_token": tok}, timeout=30).json()
    for pg in r.get("data", []):
        ig = (pg.get("instagram_business_account") or {}).get("id")
        if ig:
            return ig
    raise SystemExit(f"Brak konta Instagram przy stronie Facebook: {str(r)[:300]}")


_waited: dict = {}


def recent_posts(tok: str, ig: str, username: str) -> tuple[dict | None, str]:
    fields = (f"business_discovery.username({username})"
              f"{{username,name,followers_count,media.limit({POSTS_PER_ACCOUNT}){{caption,timestamp,permalink}}}}")
    for attempt in range(3):
        try:
            r = requests.get(f"{G}/{ig}", params={"fields": fields, "access_token": tok}, timeout=40).json()
            break
        except requests.RequestException as e:
            time.sleep(5 * (attempt + 1))
            r = {"error": {"message": str(e)}}
    if "error" in r:
        msg = r["error"].get("message", "błąd")
        if "request limit" in msg and not _waited.get(username):
            _waited[username] = True
            print(f"[limit Instagrama] czekam 20 min przy @{username}", flush=True)
            time.sleep(20 * 60)
            return recent_posts(tok, ig, username)
        return None, msg[:160]
    return r.get("business_discovery"), ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100, help="ile kont")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--redo", action="store_true", help="przeczytaj ponownie posty z ostatnich 30 dni")
    ap.add_argument("--only", default="", help="tylko te konta (po przecinku)")
    a = ap.parse_args()
    tok = os.environ["IG_ACCESS_TOKEN"].strip()
    accounts = json.load(open(os.path.join(os.path.dirname(__file__), "..", "sources", "instagram.json")))["accounts"]
    if a.only:
        want = {x.strip().lstrip("@").lower() for x in a.only.split(",") if x.strip()}
        accounts = [x for x in accounts if x["username"].lower() in want]
    accounts = accounts[: a.limit]

    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
    usage = {"input": 0, "output": 0, "calls": 0}
    client_h, usage_h = H.client_usage()
    db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"].strip())
    today = R.today_uae()
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    existing = db.get("events", {"select": "id,title,start_date,bot_key", "start_date": f"gte.{(today - dt.timedelta(days=7)).isoformat()}",
                                 "limit": "5000"})
    seen = {p["url"] for p in db.get("bot_pages", {"select": "url", "url": "like.https://www.instagram.com/*", "limit": "20000"})}
    if a.redo:
        seen = set()
    deals = db.get("deals", {"select": "title,venue,city,deal_type,days_of_week,status", "limit": "10000"})
    deals_added = 0
    ig = ig_user_id(tok)

    report, bad_accounts = [], []
    added = 0
    for acc in accounts:
        u = acc["username"]
        bd, err = recent_posts(tok, ig, u)
        if not bd:
            bad_accounts.append((u, err))
            print(f"@{u}: {err}")
            continue
        if (bd.get("followers_count") or 0) < 1000:
            bad_accounts.append((u, f"za mało obserwujących ({bd.get('followers_count')}), pewnie nie oficjalne"))
            continue
        posts = (bd.get("media") or {}).get("data", [])
        name = bd.get("name") or u
        new_here = 0
        for p in posts:
            url, cap = p.get("permalink"), (p.get("caption") or "").strip()
            try:
                posted = dt.datetime.fromisoformat(p["timestamp"].replace("+0000", "+00:00")).date()
            except (KeyError, ValueError):
                continue
            if not url or url in seen or (today - posted).days > MAX_AGE_DAYS:
                continue
            h = hashlib.sha1(cap.encode()).hexdigest()
            if not a.dry_run:
                db.upsert("bot_pages", {"url": url, "content_hash": h, "last_fetched_at": now_iso, "last_status": "instagram"}, "url")
            seen.add(url)
            if len(cap) < 40:
                continue
            text = f"Instagram post by @{u} ({name}), posted on {posted.isoformat()}.\n\n{cap}"
            if OFFER_HINT.search(cap):
                page_norm = R.norm(text)
                venue_name = acc.get("venue") or name
                for o in H.ask_offers(client_h, {"name": venue_name, "city": acc["city"]}, text, url, usage_h):
                    off, why = H.check_offer(o, page_norm)
                    if not off:
                        report.append((u, f"[oferta] {o.get('title')}", f"odrzucone: {why}"))
                        continue
                    outlet = off.pop("outlet", None)
                    venue = f"{outlet}, {venue_name}" if outlet and R.norm(outlet) not in R.norm(venue_name) else venue_name
                    row = {**off, "venue": venue, "city": acc["city"], "official_url": url, "status": "pending",
                           "source_name": f"OutToday Instagram bot (@{u}, to verify)"}
                    row = {k: v for k, v in row.items() if v not in (None, "", [])}
                    if H.is_dup(row, deals) or any(R.titles_match(e["title"], row["title"]) for e in existing):
                        report.append((u, f"[oferta] {row['title']}", "już jest w bazie"))
                        continue
                    if not a.dry_run:
                        try:
                            db.insert("deals", row)
                        except RuntimeError as e:
                            report.append((u, f"[oferta] {row['title']}", f"błąd zapisu: {str(e)[:80]}"))
                            continue
                    deals.append(row)
                    deals_added += 1
                    new_here += 1
                    report.append((u, f"[oferta] {row['title']}", f"✓ {venue} — {row.get('price_text') or 'bez ceny'}"))
            if not HINT.search(cap):
                continue
            src = {"id": f"ig_{u}", "name": f"Instagram @{u}", "city": acc["city"], "default_venue": acc.get("venue"),
                   "single_venue": bool(acc.get("venue")), "trusted": False}
            out = R.call_model(client, text, [], src, url, None, usage)
            page_norm = R.norm(text)
            for raw in out.get("events", []):
                item, why = R.check_item(raw, page_norm, set(), src, url)
                if not item:
                    report.append((u, raw.get("title"), f"odrzucone: {why}"))
                    continue
                if not item.get("start_date"):
                    report.append((u, item["title"], "odrzucone: brak daty w poście"))
                    continue
                key = R.bot_key(src["id"], item)
                sd = item["start_date"].isoformat()
                if any(e.get("bot_key") == key or (e["start_date"] == sd and R.titles_match(e["title"], item["title"])) for e in existing):
                    report.append((u, item["title"], "już jest w bazie"))
                    continue
                row = R.to_row(item, src, key, now_iso)
                row.update(status="pending", verified_at=None, source_name=f"OutToday Instagram bot (@{u}, to verify)")
                row["evidence"] = {k: v for k, v in row["evidence"].items() if k != "auto"}
                if not a.dry_run:
                    try:
                        db.insert("events", row)
                    except RuntimeError as e:
                        report.append((u, item["title"], "już jest w bazie" if "23505" in str(e) else f"błąd zapisu: {str(e)[:80]}"))
                        continue
                existing.append({"title": item["title"], "start_date": sd, "bot_key": key})
                added += 1
                new_here += 1
                report.append((u, item["title"], f"✓ {sd} {item.get('start_time') or ''} {item.get('venue') or ''} {item.get('price_text') or ''}".strip()))
            time.sleep(1)
        print(f"@{u} ({name}): postów {len(posts)}, nowych eventów/ofert {new_here}")

    print("\n| Konto | Event | Wynik |\n|---|---|---|")
    for u, t, res in report:
        print(f"| @{u} | {t} | {res} |")
    if bad_accounts:
        print("\nKonta niedostępne (zła nazwa albo konto prywatne/osobiste):")
        for u, e in bad_accounts:
            print(f"- @{u}: {e}")
    c = usage["input"] / 1e6 * 1.0 + usage["output"] / 1e6 * 5.0 + H.cost(usage_h)
    print(f"\nKonta: {len(accounts)}. Nowe eventy (do zatwierdzenia): {added}. Nowe oferty (do zatwierdzenia): {deals_added}. AI: {usage['calls']} wywołań, koszt ok. ${c:.2f}"
          + (" [próba – nic nie zapisano]" if a.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
