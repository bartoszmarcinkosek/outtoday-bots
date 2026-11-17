import os, sys, re, json, requests
sys.path.insert(0, os.path.dirname(__file__))
from instagram import ig_user_id, G
tok = os.environ["IG_ACCESS_TOKEN"].strip()
me = ig_user_id(tok)
M = re.compile(r"(?<![\w.])@([A-Za-z0-9_.]{3,30})")
for u in ["visitabudhabi", "yasisland", "dubai_calendar", "cocacolaarena"]:
    r = requests.get(f"{G}/{me}", params={"fields": f"business_discovery.username({u}){{media.limit(12){{caption}}}}", "access_token": tok}, timeout=30).json()
    caps = [p.get("caption") or "" for p in ((r.get("business_discovery") or {}).get("media") or {}).get("data", [])]
    ms = [m for c in caps for m in M.findall(c)]
    print(f"IG|{u}: {len(caps)} postów, z captionem {sum(1 for c in caps if c)}, oznaczeń {len(ms)}: {ms[:15]}")
    if caps: print("IG|  przykład:", json.dumps(caps[0][:300], ensure_ascii=False))
