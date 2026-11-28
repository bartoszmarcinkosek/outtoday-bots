"""Tylko odczyt, bez AI: sprawdza, czy kandydaci na konta Instagram istnieją i czy są aktywni."""
import os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import instagram as I
import json, collections
import ig_seen
B = os.path.join(os.path.dirname(__file__), "..")
have = {x["username"].lower() for x in json.load(open(os.path.join(B, "sources", "instagram.json")))["accounts"]}
REJ = ig_seen.load(hard_only=True)
C, VEN = collections.defaultdict(list), {}
for l in open(os.path.join(B, "audit", "ig_candidates.txt")):
    p = [x.strip() for x in l.split("|")]
    if l.startswith("#") or len(p) < 2:
        continue
    if p[1].lower() in have:
        print(f"IG|{p[0]}|{p[1]}|JUŻ JEST"); continue
    if p[1].lower() in REJ:
        print(f"IG|{p[0]}|{p[1]}|JUŻ ODRZUCONE"); continue
    C[p[0]].append(p[1]); VEN[p[1]] = p[2] if len(p) > 2 else ""
tok = os.environ["IG_ACCESS_TOKEN"].strip()
import requests, time
ig = I.ig_user_id(tok)
for city, names in C.items():
    for u in names:
        f = f"business_discovery.username({u}){{username,name,followers_count,media_count,media.limit(3){{timestamp,caption}}}}"
        try:
            r = requests.get(f"{I.G}/{ig}", params={"fields": f, "access_token": tok}, timeout=40).json()
        except Exception as e:
            print(f"IG|{city}|{u}|ERR {e}"); continue
        if "error" in r:
            m = r["error"].get("message", "")[:70]
            print(f"IG|{city}|{u}|BRAK {m}")
            if "request limit" in m:
                print("IG|limit – koniec"); sys.exit(0)
            continue
        b = r["business_discovery"]
        md = (b.get("media") or {}).get("data") or []
        last = md[0]["timestamp"][:10] if md else "-"
        cap = (md[0].get("caption") or "")[:60].replace("\n", " ") if md else ""
        print(f"IG|{city}|{u}|OK {b.get('followers_count')} obs.|ost. post {last}|{b.get('name')}|{cap}")
        time.sleep(1)
