"""Sprawdza kandydatów na konta Instagram miejsc przez oficjalne Graph API (business_discovery).
Wejście: audit/ig_check.txt, linie „Nazwa miejsca | handle”. Wyjście: linie IGC| (bez AI, bez kosztów)."""
import os, sys, time, requests
sys.path.insert(0, os.path.dirname(__file__))
from instagram import G, ig_user_id  # noqa: E402

tok = os.environ["IG_ACCESS_TOKEN"]
ig = ig_user_id(tok)
lines = [l.strip() for l in open("audit/ig_check.txt", encoding="utf-8") if "|" in l and not l.startswith("#")]
for line in lines:
    place, handle = [x.strip() for x in line.split("|", 1)]
    handle = handle.lstrip("@").strip("/")
    f = (f"business_discovery.username({handle}){{username,name,biography,website,followers_count,media_count,"
         f"media.limit(1){{timestamp}}}}")
    r = requests.get(f"{G}/{ig}", params={"fields": f, "access_token": tok}, timeout=40).json()
    if "error" in r:
        print(f"IGC|{place}|{handle}|NO|{r['error'].get('message','')[:90]}", flush=True)
    else:
        b = r.get("business_discovery", {})
        last = ((b.get("media") or {}).get("data") or [{}])[0].get("timestamp", "")[:10]
        bio = (b.get("biography") or "").replace("\n", " ")[:150]
        print(f"IGC|{place}|{handle}|OK|{b.get('name','')}|{b.get('followers_count')}|last {last}|{b.get('website') or ''}|{bio}", flush=True)
    time.sleep(1)
