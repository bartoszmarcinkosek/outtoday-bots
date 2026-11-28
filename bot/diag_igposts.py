"""Czyta ostatnie posty kont (Graph API business_discovery) i wypisuje te z danym słowem.
Wejście: audit/ig_check.txt, linie „nazwa | handle | słowo”. Wyjście: IGP| (bez AI)."""
import os, sys, time, requests
sys.path.insert(0, os.path.dirname(__file__))
from instagram import G, ig_user_id  # noqa: E402
tok = os.environ["IG_ACCESS_TOKEN"]; ig = ig_user_id(tok)
for line in [l.strip() for l in open("audit/ig_check.txt", encoding="utf-8") if l.count("|") >= 2 and not l.startswith("#")]:
    place, handle, kw = [x.strip() for x in line.split("|", 2)]
    f = f"business_discovery.username({handle}){{username,biography,media.limit(25){{caption,timestamp,permalink}}}}"
    r = requests.get(f"{G}/{ig}", params={"fields": f, "access_token": tok}, timeout=40).json()
    if "error" in r:
        print(f"IGP|{place}|{handle}|NO|{r['error'].get('message','')[:80]}", flush=True); continue
    b = r["business_discovery"]; hits = 0
    for m in (b.get("media") or {}).get("data", []):
        c = (m.get("caption") or "").replace("\n", " ")
        if kw.lower() in c.lower():
            hits += 1; print(f"IGP|{place}|{handle}|{m['timestamp'][:10]}|{m['permalink']}|{c[:400]}", flush=True)
    if not hits: print(f"IGP|{place}|{handle}|no posts with '{kw}'|bio: {(b.get('biography') or '')[:120]}", flush=True)
    time.sleep(1)
