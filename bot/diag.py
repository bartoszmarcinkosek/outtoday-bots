import os, requests
tok = os.environ.get("IG_ACCESS_TOKEN", "").strip()
G = "https://graph.facebook.com/v21.0"
p = requests.get(f"{G}/me/permissions", params={"access_token": tok}, timeout=30).json()
print("PERMS", [(x["permission"], x["status"]) for x in p.get("data", [])], p.get("error"))
acc = requests.get(f"{G}/me/accounts", params={"fields": "name,access_token,instagram_business_account{id}", "access_token": tok}, timeout=30).json()
for pg in acc.get("data", []):
    ig = (pg.get("instagram_business_account") or {}).get("id")
    if not ig: continue
    for label, t in (("user", tok), ("page", pg.get("access_token"))):
        r = requests.get(f"{G}/{ig}", params={"fields": "business_discovery.username(atlantisthepalm){username,media_count}", "access_token": t}, timeout=30).json()
        print("DISCOVERY", label, str(r)[:300])
