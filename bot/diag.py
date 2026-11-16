import os, requests
tok = os.environ.get("IG_ACCESS_TOKEN", "").strip()
print("TOKEN set:", bool(tok), "length:", len(tok))
if tok:
    r = requests.get("https://graph.facebook.com/v21.0/me", params={"fields": "id,name,instagram_business_account{id,username}", "access_token": tok}, timeout=30)
    d = r.json()
    print("STATUS", r.status_code, {k: v for k, v in d.items() if k != "access_token"})
    ig = (d.get("instagram_business_account") or {}).get("id")
    if ig:
        q = f"business_discovery.username(atlantisthepalm){{username,media.limit(2){{caption,timestamp}}}}"
        r2 = requests.get(f"https://graph.facebook.com/v21.0/{ig}", params={"fields": q, "access_token": tok}, timeout=30)
        bd = r2.json()
        print("DISCOVERY", r2.status_code, str(bd)[:400])
