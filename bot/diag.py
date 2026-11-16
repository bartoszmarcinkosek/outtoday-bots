import os, requests
tok = os.environ["IG_ACCESS_TOKEN"].strip(); G = "https://graph.facebook.com/v21.0"
acc = requests.get(f"{G}/me/accounts", params={"fields": "instagram_business_account{id}", "access_token": tok}, timeout=30).json()
ig = next(p["instagram_business_account"]["id"] for p in acc["data"] if p.get("instagram_business_account"))
for u in ["dubai_calendar", "dubaicalendarofficial", "dubaiparksnresorts", "dubaiparks", "dubai_marathon", "dubaimarathonofficial", "adnocdubaimarathon",
          "platinumlistnet", "platinumlist", "livenationme", "virginmegastoreme", "virginmegastoreuae", "feverdubai", "fever.dubai", "candlelight.dubai",
          "ferrariworldyas", "wbworldabudhabi", "seaworldyasisland", "teamlabphenomenaad", "emiratespalacemo", "dct_abudhabi", "qasralwatan", "visitalain",
          "mleihasharjah", "aljadasharjah", "jebeljais", "visitajman", "visitfujairah", "dubaifitnesschallenge", "dubaishoppingfestival", "dubaifoodfestival",
          "theviewatthepalm", "dubaiframe", "laperledubai", "theatreofdigitalart", "abudhabiculture", "yasbayabudhabi", "alqanaabudhabi", "abudhabiartfair",
          "houseofwisdomshj", "sharjahmuseums", "visitrasalkhaimah", "visitsharjah", "yaswaterworld", "culturalfoundation", "manaratalsaadiyat"]:
    r = requests.get(f"{G}/{ig}", params={"fields": f"business_discovery.username({u}){{username,name,followers_count}}", "access_token": tok}, timeout=30).json()
    bd = r.get("business_discovery")
    print("IGCHK", u, "->", (bd["name"], bd.get("followers_count")) if bd else r.get("error", {}).get("message", "")[:60])
