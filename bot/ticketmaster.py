"""Ticketmaster Discovery API → eventy w ZEA. Bez AI, koszt 0.

Dane są uporządkowane (data, godzina, miejsce, cena), więc nie wysyłamy nic do AI.
Działa dopiero, gdy w GitHub Secrets jest TICKETMASTER_KEY (darmowy klucz z developer.ticketmaster.com).
Uruchomienie: python bot/ticketmaster.py [--dry-run]
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
from run import DB, titles_match  # noqa: E402

SOURCE = "Ticketmaster"
API = "https://app.ticketmaster.com/discovery/v2/events.json"
CAT = {"Music": "music", "Sports": "sport", "Arts & Theatre": "culture", "Family": "family", "Film": "culture"}
CITY = {"dubai": "Dubai", "abu dhabi": "Abu Dhabi", "al ain": "Al Ain", "sharjah": "Sharjah", "ajman": "Ajman",
        "ras al khaimah": "Ras Al Khaimah", "fujairah": "Fujairah", "umm al quwain": "Umm Al Quwain"}


def fetch_all(key: str) -> list[dict]:
    out: list[dict] = []
    for page in range(10):
        r = requests.get(API, params={"apikey": key, "countryCode": "AE", "size": 100, "page": page, "sort": "date,asc"}, timeout=30)
        if r.status_code != 200:
            print(f"  API: {r.status_code} {r.text[:150]}")
            break
        data = r.json()
        evs = (data.get("_embedded") or {}).get("events", [])
        out += evs
        if page + 1 >= (data.get("page") or {}).get("totalPages", 0):
            break
    return out


def to_item(ev: dict, today: str) -> tuple[dict | None, str]:
    st = (ev.get("dates") or {}).get("start") or {}
    sd = st.get("localDate")
    if not sd or sd < today:
        return None, "brak daty albo minione"
    if ((ev.get("dates") or {}).get("status") or {}).get("code") in ("cancelled", "postponed"):
        return None, "odwołane / przełożone"
    v = ((ev.get("_embedded") or {}).get("venues") or [{}])[0]
    city = CITY.get(((v.get("city") or {}).get("name") or "").lower())
    if not city:
        return None, "nieznane emirat"
    venue = v.get("name")
    if not venue:
        return None, "brak miejsca"
    t = st.get("localTime")
    pr = (ev.get("priceRanges") or [{}])[0]
    price = pmin = None
    if pr.get("min") is not None and pr.get("currency"):
        price = f"From {pr['currency']} {float(pr['min']):g}"
        pmin = round(float(pr["min"])) if pr["currency"] == "AED" else None
    seg = (((ev.get("classifications") or [{}])[0]).get("segment") or {}).get("name") or ""
    end = ((ev.get("dates") or {}).get("end") or {}).get("localDate")
    gaps = [g for g, ok in (("price", price is not None), ("start_time", bool(t))) if not ok]
    return {
        "title": (ev.get("name") or "").strip(), "description": None, "category": CAT.get(seg, "culture"),
        "start_date": sd, "end_date": end if end and end != sd else None, "start_time": (t or "")[:5] or None,
        "venue": venue, "city": city, "price_text": price, "price_min_aed": pmin, "is_free": False,
        "url": ev.get("url"), "official_url": ev.get("url"), "source_name": SOURCE, "source_url": ev.get("url"),
        "status": "pending", "bot_key": f"ticketmaster:{ev['id']}", "gaps": gaps,
        "evidence": {"page": ev.get("url"), "api": "Ticketmaster Discovery API v2"},
    }, ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    key = os.environ.get("TICKETMASTER_KEY", "").strip()
    if not key:
        print("Brak TICKETMASTER_KEY: pomijam Ticketmaster.")
        return 0
    db = DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=4))).date().isoformat()
    now_iso = dt.datetime.now(dt.timezone.utc).isoformat()
    evs = fetch_all(key)
    print(f"Ticketmaster: {len(evs)} wydarzeń w ZEA")
    existing = db.get("events", {"select": "title,start_date", "start_date": f"gte.{today}", "limit": "5000"})
    keys = {e.get("bot_key") for e in db.get("events", {"select": "bot_key", "bot_key": "like.ticketmaster:*", "limit": "5000"})}
    added = 0
    for ev in evs:
        if f"ticketmaster:{ev.get('id')}" in keys:
            continue
        item, why = to_item(ev, today)
        if not item:
            continue
        if any(e["start_date"] == item["start_date"] and titles_match(e["title"], item["title"]) for e in existing):
            continue
        print(f"  + {item['title'][:70]} | {item['start_date']} {item['start_time'] or ''} | {item['venue'][:40]} | {item['price_text']}")
        if not args.dry_run:
            item["last_seen_at"] = now_iso
            db.insert("events", item)
        existing.append({"title": item["title"], "start_date": item["start_date"]})
        added += 1
    print(f"Ticketmaster: nowe {added}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
