import os, requests
tok = os.environ["IG_ACCESS_TOKEN"].strip(); G = "https://graph.facebook.com/v21.0"
acc = requests.get(f"{G}/me/accounts", params={"fields": "instagram_business_account{id}", "access_token": tok}, timeout=30).json()
ig = next(p["instagram_business_account"]["id"] for p in acc["data"] if p.get("instagram_business_account"))
for u in ["thefriskyfox", "friskyfoxrak", "thefriskyfoxrak", "alhamravillage", "alhamravillagehotel", "alhamragolfclub", "alhamragolf", "thebayrak", "thebay_rak"]:
    r = requests.get(f"{G}/{ig}", params={"fields": f"business_discovery.username({u}){{username,name,followers_count}}", "access_token": tok}, timeout=30).json()
    bd = r.get("business_discovery")
    print("IGCHK", u, "->", (bd["name"], bd.get("followers_count")) if bd else r.get("error", {}).get("message", "")[:60])
