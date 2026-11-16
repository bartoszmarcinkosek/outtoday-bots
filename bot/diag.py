import os, requests
tok = os.environ.get("IG_ACCESS_TOKEN", "").strip()
G = "https://graph.facebook.com/v21.0"
me = requests.get(f"{G}/me", params={"fields": "id,name", "access_token": tok}, timeout=30).json()
print("ME", {k: v for k, v in me.items() if k in ("name", "error")})
acc = requests.get(f"{G}/me/accounts", params={"fields": "name,instagram_business_account{id,username}", "access_token": tok}, timeout=30).json()
print("ACCOUNTS", [{"name": p.get("name"), "ig": p.get("instagram_business_account")} for p in acc.get("data", [])], acc.get("error"))
ig = next((p["instagram_business_account"]["id"] for p in acc.get("data", []) if p.get("instagram_business_account")), None)
if ig:
    q = "business_discovery.username(atlantisthepalm){username,media.limit(2){caption,timestamp}}"
    r2 = requests.get(f"{G}/{ig}", params={"fields": q, "access_token": tok}, timeout=30).json()
    print("DISCOVERY", str(r2)[:400])
