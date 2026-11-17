import os, sys, requests, json
sys.path.insert(0, os.path.dirname(__file__))
from instagram import ig_user_id, G
tok = os.environ["IG_ACCESS_TOKEN"].strip()
me = ig_user_id(tok)
u = os.environ.get("U", "poloniadubai")
r = requests.get(f"{G}/{me}", params={"fields": f"business_discovery.username({u}){{username,name,biography,website,followers_count,media_count,media.limit(6){{caption,timestamp,permalink}}}}", "access_token": tok}, timeout=30).json()
print("IG|" + json.dumps(r, ensure_ascii=False)[:3000])
