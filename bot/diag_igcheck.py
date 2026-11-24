"""Tylko odczyt, bez AI: sprawdza, czy kandydaci na konta Instagram istnieją i czy są aktywni."""
import os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import instagram as I
C = {
 "Al Ain": ["alainmall", "bawadimall", "hilifuncity", "danatalainresort", "aylahotels", "alainfc", "adnecalain", "alainoasis", "jimimall", "alainequestrian", "radissonblualain", "alainpalacehotel", "remalmall", "alainclub", "greenmubazzarah", "alaincityae", "visitalain", "ayla_grand_hotel", "herirooms"],
 "Ajman": ["ajmansaray", "bahiajmanpalace", "ajmanhotel", "wyndhamgardenajman", "ajmantourism", "alzorah", "oberoialzorah", "ajmanmarina", "ajmanmuseum", "ramadabeachajman", "radissonblu_ajman", "ajmanstud", "ajman_events", "ajmanmediacity", "ajmanclub", "thecornerajman"],
 "Umm Al Quwain": ["vidabeachresortuaq", "kitebeachcenter", "dreamlanduae", "uaqmarineclub", "pearlhoteluaq", "barracudabeachresort", "uaq.tourism", "uaqtourism", "kitebeachuaq", "mangrovebeachuaq", "casadelmaruaq", "uaqgov", "royalbeachuaq"],
 "Fujairah": ["lemeridienalaqah", "intercontinentalfujairah", "addressbeachresortfujairah", "palacefujairah", "royalmfujairah", "fujairahfort", "umbrellabeachfujairah", "albaharbeach", "fujairahmall", "luluhypermarketfujairah", "dibbabayoysters", "snoopyislandfujairah", "fujairah_fc", "fujairahgov", "alaqahbeachresort", "miramaralaqah", "fujairahcrownprince_award", "fujairahfineartsacademy", "novotelfujairah", "concordefujairah"],
}
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
