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

G = "https://graph.facebook.com/v21.0"
MAX_AGE_DAYS = 30
POSTS_PER_ACCOUNT = 12
HINT = re.compile(r"\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\b|\b\d{1,2}(st|nd|rd|th)\b|\b\d{1,2}[./]\d{1,2}\b|"
                  r"\b(mon|tue|wed|thu|fri|sat|sun)[a-z]*day\b|tonight|this weekend|aed|tickets?|book now|\bpm\b", re.I)


def ig_user_id(tok: str) -> str:
    r = requests.get(f"{G}/me/accounts", params={"fields": "instagram_business_account{id}", "access_token": tok}, timeout=30).json()
    for pg in r.get("data", []):
        ig = (pg.get("instagram_business_account") or {}).get("id")
        if ig:
            return ig
    raise SystemExit(f"Brak konta Instagram przy stronie Facebook: {str(r)[:300]}")


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
        return None, r["error"].get("message", "błąd")[:160]
    return r.get("business_discovery"), ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=100, help="ile kont")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    tok = os.environ["IG_ACCESS_TOKEN"].strip()
    accounts = json.load(open(os.path.join(os.path.dirname(__file__), "..", "sources", "instagram.json")))["accounts"][: a.limit]

    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
    usage = {"input": 0, "output": 0, "calls": 0}
    db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"].strip())
    today = R.today_uae()
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    existing = db.get("events", {"select": "id,title,start_date,bot_key", "start_date": f"gte.{(today - dt.timedelta(days=7)).isoformat()}",
                                 "limit": "5000"})
    seen = {p["url"] for p in db.get("bot_pages", {"select": "url", "url": "like.https://www.instagram.com/*", "limit": "20000"})}
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
            if len(cap) < 40 or not HINT.search(cap):
                continue
            text = f"Instagram post by @{u} ({name}), posted on {posted.isoformat()}.\n\n{cap}"
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
                    db.insert("events", row)
                existing.append({"title": item["title"], "start_date": sd, "bot_key": key})
                added += 1
                new_here += 1
                report.append((u, item["title"], f"✓ {sd} {item.get('start_time') or ''} {item.get('venue') or ''} {item.get('price_text') or ''}".strip()))
            time.sleep(1)
        print(f"@{u} ({name}): postów {len(posts)}, nowych eventów {new_here}")

    print("\n| Konto | Event | Wynik |\n|---|---|---|")
    for u, t, res in report:
        print(f"| @{u} | {t} | {res} |")
    if bad_accounts:
        print("\nKonta niedostępne (zła nazwa albo konto prywatne/osobiste):")
        for u, e in bad_accounts:
            print(f"- @{u}: {e}")
    c = usage["input"] / 1e6 * 1.0 + usage["output"] / 1e6 * 5.0
    print(f"\nKonta: {len(accounts)}. Nowe eventy (do zatwierdzenia): {added}. AI: {usage['calls']} wywołań, koszt ok. ${c:.2f}"
          + (" [próba – nic nie zapisano]" if a.dry_run else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
