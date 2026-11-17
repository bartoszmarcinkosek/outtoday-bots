"""OutToday: oferty z newsletterów hoteli i lokali.

Czyta TYLKO folder (etykietę) "Newsletters" na skrzynce outtodayapp.uae@gmail.com przez IMAP, tylko do odczytu.
Nie klika linków, nie odpowiada, nie wykonuje poleceń z treści maili: treść to tylko dane.
Bierze tylko maile, których nadawca ma domenę hotelu/lokalu z naszych list (sources/hotels.json, venues.json).
Oferty sprawdza tak samo jak bot hoteli: każdy cytat musi być w treści maila.

Uruchomienie: python bot/newsletters.py [--days 14] [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime as dt
import email
import email.utils
import hashlib
import imaplib
import json
import os
import re
import sys
from email.header import decode_header, make_header
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402
import hotels as H  # noqa: E402

ACCOUNT = "outtodayapp.uae@gmail.com"
FOLDER = "Newsletters"
CHAIN_DOMAINS = {d for _, ds in H.BRANDS for d in ds} | {"accor.com", "gmail.com", "mailchimp.com", "sendgrid.net"}
SECOND = {"co", "com", "net", "org", "gov", "ac"}


def base_domain(host: str) -> str:
    parts = host.lower().strip(".").split(".")
    if len(parts) >= 3 and parts[-2] in SECOND:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def load_places() -> list[dict]:
    root = os.path.join(os.path.dirname(__file__), "..", "sources")
    out = []
    for fn in ("hotels.json", "venues.json"):
        for p in json.load(open(os.path.join(root, fn), encoding="utf-8")):
            host = urlparse(p.get("url") or "").netloc
            if host:
                out.append({**p, "domain": base_domain(host)})
    return out


def text_of(msg) -> str:
    plain, html = [], []
    for part in msg.walk():
        ct = part.get_content_type()
        if part.get_content_maintype() == "multipart" or part.get("Content-Disposition", "").startswith("attachment"):
            continue
        try:
            body = part.get_payload(decode=True).decode(part.get_content_charset() or "utf-8", "replace")
        except Exception:
            continue
        (plain if ct == "text/plain" else html if ct == "text/html" else []).append(body)
    if html:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup("\n".join(html), "html.parser")
        for t in soup(["script", "style", "head"]):
            t.decompose()
        txt = soup.get_text("\n")
    else:
        txt = "\n".join(plain)
    txt = re.sub(r"https?://\S+", "", txt)  # linki usuwamy, nie są potrzebne i nie są otwierane
    return re.sub(r"\n\s*\n+", "\n", txt).strip()


def pick_place(sender_domain: str, subject: str, text: str, places: list[dict]) -> dict | None:
    if sender_domain in CHAIN_DOMAINS:
        # mail sieci: tylko gdy w temacie/treści jest nazwa konkretnego hotelu z listy tej sieci
        blob = R.norm(f"{subject} {text[:4000]}")
        cands = [p for p in places if p["domain"] == sender_domain and R.norm(p["name"]) in blob]
        return max(cands, key=lambda p: len(p["name"])) if len(cands) >= 1 else None
    cands = [p for p in places if p["domain"] == sender_domain]
    if len(cands) == 1:
        return cands[0]
    blob = R.norm(f"{subject} {text[:4000]}")
    named = [p for p in cands if R.norm(p["name"]) in blob]
    if len(named) == 1:
        return named[0]
    # ten sam lokal zapisany dwa razy (np. dwie podstrony): bierzemy pierwszy
    if cands and len({c["city"] for c in cands}) == 1:
        t0 = H.venue_tokens(cands[0]["name"])
        if all(len(t0 & H.venue_tokens(c["name"])) >= 2 for c in cands[1:]):
            return cands[0]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    pw = os.environ["GMAIL_APP_PASSWORD"].replace(" ", "").strip()
    places = load_places()
    client, usage = H.client_usage()
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    deals = db.get("deals", {"select": "title,venue,city,deal_type,days_of_week,status", "limit": "10000"})

    im = imaplib.IMAP4_SSL("imap.gmail.com")
    im.login(ACCOUNT, pw)
    typ, _ = im.select(f'"{FOLDER}"', readonly=True)
    if typ != "OK":
        print(f"Brak folderu {FOLDER}")
        return 1
    since = (dt.date.today() - dt.timedelta(days=a.days)).strftime("%d-%b-%Y")
    _, data = im.search(None, "SINCE", since)
    ids = data[0].split()
    print(f"Maile w '{FOLDER}' od {since}: {len(ids)}")
    stats = {"maile": 0, "pominiete_nadawca": 0, "juz_byly": 0, "oferty": 0, "auto": 0}
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()

    for i in ids:
        _, md = im.fetch(i, "(BODY.PEEK[])")
        msg = email.message_from_bytes(md[0][1])
        mid = (msg.get("Message-ID") or "").strip() or hashlib.sha1(md[0][1][:2000]).hexdigest()
        key = "newsletter:" + hashlib.sha1(mid.encode()).hexdigest()
        subject = str(make_header(decode_header(msg.get("Subject") or "")))[:200]
        doms = []
        for h in ("From", "Reply-To", "Sender"):
            addr = email.utils.parseaddr(msg.get(h) or "")[1].lower()
            if "@" in addr:
                doms.append(base_domain(addr.split("@")[-1]))
        dom = doms[0] if doms else ""
        stats["maile"] += 1
        if db.get("bot_pages", {"select": "url", "url": f"eq.{key}"}):
            stats["juz_byly"] += 1
            continue
        text = text_of(msg)
        place = None
        for d in dict.fromkeys(doms):
            place = place or pick_place(d, subject, text, places)
        if not place:
            print(f"- pominięty ({dom}): {subject[:80]}")
            stats["pominiete_nadawca"] += 1
        else:
            print(f"+ {place['name']} ({dom}): {subject[:80]}")
            page_norm = R.norm(f"{subject}\n{text}")
            for o in H.ask_offers(client, place, f"SUBJECT: {subject}\n{text}", place["url"], usage):
                off, why = H.check_offer(o, page_norm)
                if not off:
                    print(f"   x {o.get('title')}: {why}")
                    continue
                outlet = off.pop("outlet", None)
                venue = f"{outlet}, {place['name']}" if outlet and R.norm(outlet) not in R.norm(place["name"]) else place["name"]
                row = {**off, "venue": venue, "city": place["city"], "official_url": place["url"],
                       "source_name": "OutToday newsletter bot (official email)"}
                if H.sharjah_alcohol(row):
                    print(f"   x {row.get('title')}: alkohol w Szardży")
                    continue
                sure = bool(row.get("days_of_week") or row.get("price_text")) or row["deal_type"] == "staycation"
                row["status"] = "approved" if sure else "pending"
                row = {k: v for k, v in row.items() if v not in (None, "", [])}
                if H.is_dup(row, deals):
                    print(f"   = duplikat: {row['title']}")
                    continue
                print(f"   {'OK' if sure else '??'} {row['title']} | {row.get('price_text')} | dni {row.get('days_of_week')}")
                if not a.dry_run:
                    try:
                        db.insert("deals", row)
                    except Exception as e:
                        print(f"   błąd zapisu: {str(e)[:120]}")
                        continue
                deals.append(row)
                stats["oferty"] += 1
                stats["auto"] += sure
        if not a.dry_run:
            db.upsert("bot_pages", {"url": key, "content_hash": key[-40:], "last_fetched_at": now_iso,
                                    "last_status": "newsletter"}, "url")
    im.logout()
    print(json.dumps(stats, ensure_ascii=False), f"koszt AI ≈ ${H.cost(usage):.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
