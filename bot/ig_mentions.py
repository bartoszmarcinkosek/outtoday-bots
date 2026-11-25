"""OutToday: nowe konta Instagram z oznaczeń (@...) w postach oficjalnych kont turystycznych / miejsc.

1. Czyta ostatnie posty kont-"węzłów" (urzędy turystyki, kalendarze, wyspy, areny) i zbiera oznaczenia @konto.
2. Kandydatów sortuje wg liczby oznaczeń i sprawdza przez Instagram Graph API:
   min. 1000 obserwujących, w opisie / stronie www widać miasto w UAE (to ustala też miasto konta).
3. Wynik: tabela do przejrzenia; bez --save nic nie zapisuje (próba).
Uruchomienie: python bot/ig_mentions.py [--max-new 200] [--save]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import re
import sys
import time

import requests

sys.path.insert(0, os.path.dirname(__file__))
import instagram as IG  # noqa: E402

IG_FILE = os.path.join(os.path.dirname(__file__), "..", "sources", "instagram.json")
HUBS = ["dubai_calendar", "visitdubai", "dubaiculture", "visitabudhabi", "abudhabiculture", "yasisland", "saadiyatae",
        "visitrasalkhaimah", "visit_shj", "shjtourism", "sharjahmuseums", "fujairahtourism", "visitummalquwain", "ajman",
        "dubaiharbour", "bluewatersdubai", "yasbayuae", "expocitydubai", "globalvillageuae", "dubaimall", "livenationme",
        "etihadarena.ae", "cocacolaarena", "dubaiopera", "alserkalavenue", "madinatjumeirah", "soukmadinatjumeirah",
        "visit.hatta", "eidaletihad", "dubaifitnesschallenge", "thegalleriauae", "marjanrak", "alainzoouae"]
EXTRA_HUBS = ["khorfakkanbeach", "khorfakkanamphitheatre", "almajazwaterfront", "alnoorisland", "discovermleiha", "shurooqsharjah",
              "citycentrefujairah", "fujairahmalluae", "albaharhotelandresort", "sharjahgsc", "shjladiesclub", "sharjahart"]
PLAIN = re.compile(r"(?<![\w@./-])([a-z0-9]{2,}(?:[._][a-z0-9]{2,}){1,3}|[a-z]{4,24}(?:dubai|uae|abudhabi|dxb|auh|rak|shj|sharjah|ajman|fujairah|alain|hotel|resort|mall|beach|club|events|festival)\b)(?![\w/-])")
JUNK = re.compile(r"^www\.|\.(com|net|org|co|io|me|ly|info|gov)$|^\d|\.\d+$", re.I)
MENTION = re.compile(r"(?<![\w.])@([A-Za-z0-9_.]{3,30})")
CITY = [("Abu Dhabi", r"abu ?dhabi|abudhabi|yas island|saadiyat|\bauh\b"), ("Al Ain", r"al ?ain"),
        ("Ras Al Khaimah", r"ras al khaimah|\brak\b|al hamra|marjan"), ("Sharjah", r"sharjah|\bshj\b"),
        ("Fujairah", r"fujairah"), ("Ajman", r"ajman"), ("Umm Al Quwain", r"umm al quwain|\buaq\b"),
        ("Dubai", r"dubai|\bdxb\b|jumeirah|palm jumeirah|difc|jbr|marina")]
PERSONAL = re.compile(r"influencer|blogger|content creator|creator|model|photographer|ugc|personal|my life|mum of|mom of|"
                      r"dm for collab|collab|real estate agent|realtor|coach\b|dj\b|artist\b|chef\b", re.I)
SKIP = {"instagram", "visitdubai", "dubai_calendar"}


def info(tok, ig, u):
    f = f"business_discovery.username({u}){{username,name,biography,website,followers_count,media_count}}"
    for _ in range(2):
        r = requests.get(f"{IG.G}/{ig}", params={"fields": f, "access_token": tok}, timeout=40).json()
        if "error" in r and "request limit" in r["error"].get("message", ""):
            print("[limit Instagrama] czekam 20 min", flush=True)
            time.sleep(1200)
            continue
        return r.get("business_discovery"), (r.get("error") or {}).get("message", "")[:80]
    return None, "limit"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-new", type=int, default=200)
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args()
    tok = os.environ["IG_ACCESS_TOKEN"].strip()
    ig = IG.ig_user_id(tok)
    data = json.load(open(IG_FILE, encoding="utf-8"))
    have = {x["username"].lower() for x in data["accounts"]}
    counts, by = collections.Counter(), collections.defaultdict(set)
    # 25.11.2026: węzłami są też wszystkie nasze konta bez przypisanego miejsca (urzędy, kalendarze, organizatorzy, dzielnice)
    # oraz konta dzielnic i centrów – one najczęściej oznaczają lokale i organizatorów.
    hubs = list(dict.fromkeys(HUBS + [x["username"] for x in data["accounts"] if not x.get("venue")] + EXTRA_HUBS))
    print(f"Węzłów: {len(hubs)}")
    for h in hubs:
        bd, err = IG.recent_posts(tok, ig, h)
        if not bd:
            print(f"  @{h}: brak ({err})", flush=True)
            continue
        print(f"  @{h}: {len((bd.get('media') or {}).get('data', []))} postów", flush=True)
        for p in (bd.get("media") or {}).get("data", []):
            cap = p.get("caption") or ""
            # API Instagrama usuwa znak @ z opisów cudzych postów (zostaje sama nazwa konta jako zwykłe słowo),
            # więc oprócz @nazwa łapiemy też słowa wyglądające jak nazwa konta: z kropką/podkreśleniem
            # albo jedno małe słowo zakończone typową końcówką (…dubai, …uae, …hotel, …mall).
            found = set(MENTION.findall(cap)) | {t for t in PLAIN.findall(cap) if not JUNK.search(t)}
            for m in found:
                m = m.rstrip(".").lower()
                if m not in have and m not in SKIP:
                    counts[m] += 1
                    by[m].add(h)
        time.sleep(1)
    print(f"Kandydatów z oznaczeń: {len(counts)}")
    added, rep = [], []
    for u, n in counts.most_common(400):
        if len(added) >= a.max_new:
            break
        bd, err = info(tok, ig, u)
        time.sleep(1.5)
        if not bd:
            rep.append((u, n, f"niedostępne ({err})"))
            continue
        fol = bd.get("followers_count") or 0
        text = f"{bd.get('name') or ''} {bd.get('biography') or ''} {bd.get('website') or ''}"
        city = next((c for c, rx in CITY if re.search(rx, text, re.I)), None)
        if fol < 1000:
            rep.append((u, n, f"za mało obserwujących ({fol})"))
        elif not city:
            rep.append((u, n, "brak UAE w opisie/stronie"))
        elif PERSONAL.search(text):
            rep.append((u, n, "wygląda na konto osoby / twórcy"))
        else:
            added.append({"username": u, "city": city})
            have.add(u)
            rep.append((u, n, f"✓ {bd.get('name')} · {fol} · {city} · {(bd.get('website') or '')[:40]} · oznaczone przez {', '.join(sorted(by[u]))[:60]}"))
    print("\n| Konto | Oznaczeń | Wynik |\n|---|---|---|")
    for u, n, res in rep:
        print(f"| @{u} | {n} | {res} |")
    if a.save and added:
        data["accounts"].extend(added)
        json.dump(data, open(IG_FILE, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(f"\nNowe konta: {len(added)}" + ("" if a.save else " [próba – nic nie zapisano]"),
          dict(collections.Counter(x["city"] for x in added)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
