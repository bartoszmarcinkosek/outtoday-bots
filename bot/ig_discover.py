"""OutToday: szuka oficjalnych kont Instagram na oficjalnych stronach z naszych list.

1. Bierze strony z sources/hotels.json, sources/venues.json i źródeł eventów (sources/*.json).
2. Pobiera stronę (z poszanowaniem robots.txt) i wyciąga linki instagram.com/<konto>.
3. Konto użyte przez wiele różnych miejsc (np. konto sieci hoteli) jest pomijane.
4. Każde konto sprawdza przez Instagram Graph API: musi istnieć i mieć min. 1000 obserwujących.
5. Dopisuje nowe konta do sources/instagram.json (miasto + miejsce ze strony, na której był link).

Bez AI: koszt zero. Uruchomienie: python bot/ig_discover.py [--dry-run] [--limit 1000]
"""

from __future__ import annotations

import argparse
import collections
import glob
import json
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402
import instagram as IG  # noqa: E402

SRC = os.path.join(os.path.dirname(__file__), "..", "sources")
IG_FILE = os.path.join(SRC, "instagram.json")
HANDLE = re.compile(r"instagram\.com/(?!p/|reel/|explore/|stories/|accounts/|share)([A-Za-z0-9_.]{2,30})", re.I)
SKIP = {"instagram", "about", "developer", "legal", "direct", "tv", "web",
        # konta sieci / obce / nieoficjalne grupy (sprawdzone ręcznie 17.11)
        "africanqueen_beaulieusurmer", "barcelohotelsresorts", "daysinn", "bangaloresinglesnetwork", "ginger_universaldma",
        "emaardubai", "marriottbonvoy", "hilton", "ihg", "accorhotels", "radissonhotels", "wyndhamhotels", "rotana",
        "meetup", "fever", "platinumlist", "eventbrite", "tiktok", "facebook"}


def pages() -> list[dict]:
    out = []
    for f in ("hotels.json", "venues.json"):
        for x in json.load(open(os.path.join(SRC, f), encoding="utf-8")):
            out.append({"name": x["name"], "city": x["city"], "url": x["url"]})
    for f in glob.glob(os.path.join(SRC, "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        if isinstance(d, dict) and isinstance(d.get("sources"), list):
            for s in d["sources"]:
                for u in (s.get("urls") or [])[:1]:
                    out.append({"name": s.get("default_venue") or s.get("name"), "city": s.get("city"), "url": u,
                                "single": False})
    return [p for p in out if p.get("url") and p.get("city")]


def handles_on(url: str, br) -> set[str]:
    html = ""
    try:
        r = requests.get(url, headers={"User-Agent": R.USER_AGENT}, timeout=30)
        if r.status_code < 400:
            html = r.text
    except requests.RequestException:
        pass
    found = {h.rstrip(".").lower() for h in HANDLE.findall(html)}
    if not found and br is not None:
        try:
            page = br.fetch(url)
            found = {h.rstrip(".").lower() for _, link in page.get("links") or [] for h in HANDLE.findall(link or "")}
        except Exception:
            pass
    return {h for h in found if h not in SKIP}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--limit", type=int, default=1000)
    a = ap.parse_args()
    tok = os.environ["IG_ACCESS_TOKEN"].strip()
    data = json.load(open(IG_FILE, encoding="utf-8"))
    have = {x["username"].lower() for x in data["accounts"]}
    plist = pages()[: a.limit]
    seen_url, where = set(), collections.defaultdict(list)
    with R.Browser() as br:
        for p in plist:
            if p["url"] in seen_url:
                continue
            seen_url.add(p["url"])
            ok, why = R.robots_allows(p["url"])
            if not ok:
                continue
            hs = handles_on(p["url"], br)
            for h in hs:
                where[h].append(p)
            print(f"{p['name']} ({p['city']}): {', '.join(sorted(hs)) or '-'}")
    ig = IG.ig_user_id(tok)
    added, report = [], []
    for h, ps in sorted(where.items()):
        if h in have:
            continue
        names = {R.norm(x["name"] or "") for x in ps}
        if len(names) > 2:
            report.append((h, f"pominięte: konto sieci/wspólne ({len(names)} miejsc)"))
            continue
        for wait in range(7):
            bd, err = IG.recent_posts(tok, ig, h)
            if bd or "request limit" not in err:
                break
            print(f"[limit Instagrama] czekam 20 min (sprawdzone: {len(report)})", flush=True)
            time.sleep(20 * 60)
        time.sleep(2)
        if not bd:
            report.append((h, f"niedostępne: {err[:60]}"))
            continue
        fol = bd.get("followers_count") or 0
        if fol < 1000:
            report.append((h, f"za mało obserwujących ({fol})"))
            continue
        p = ps[0]
        acc = {"username": h, "city": p["city"]}
        if p.get("name") and p.get("single", True):
            acc["venue"] = p["name"]
        added.append(acc)
        have.add(h)
        report.append((h, f"✓ {bd.get('name')} · {fol} obserwujących · {p['city']} · {p['name']}"))
    print("\n| Konto | Wynik |\n|---|---|")
    for h, res in report:
        print(f"| @{h} | {res} |")
    if added and not a.dry_run:
        data["accounts"].extend(added)
        json.dump(data, open(IG_FILE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"\nStron: {len(seen_url)}. Nowe konta: {len(added)}. Razem kont: {len(data['accounts']) if not a.dry_run else len(have)}"
          + (" [próba – nic nie zapisano]" if a.dry_run else ""))
    print("Miasta nowych kont:", dict(collections.Counter(x["city"] for x in added)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
