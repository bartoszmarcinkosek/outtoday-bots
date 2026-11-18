import os, sys, re, requests
sys.path.insert(0, os.path.dirname(__file__))
from instagram import ig_user_id, G
H = {"User-Agent": "Mozilla/5.0 (compatible; OutTodayBot/1.0)"}
for u in ["https://fujairah.platinumlist.net/", "https://ajman.platinumlist.net/", "https://umm-al-quwain.platinumlist.net/", "https://ras-al-khaimah.platinumlist.net/", "https://sharjah.platinumlist.net/",
          "https://www.hopasports.com/en/tad", "https://www.hopasports.com/ajmantourism", "https://visit-ajman.ae/en/activities/upcoming-events", "https://visitummalquwain.ae/en/events", "https://visitummalquwain.ae/"]:
    try:
        r = requests.get(u, headers=H, timeout=25, allow_redirects=True)
        ev = set(re.findall(r'/event-tickets/[^"\'\s<>]+', r.text))
        print(f"S|{u} -> {r.status_code} {r.url} len={len(r.text)} event_links={len(ev)} {sorted(ev)[:6]}")
    except Exception as e:
        print(f"S|{u} ERR {e}")
tok = os.environ["IG_ACCESS_TOKEN"].strip(); me = ig_user_id(tok)
for h in ["fujairahadventures","fujairahadventurecenter","fujairah_culture","fujairahculture","fujairahfort","fujairahcitycentre","citycentrefujairah","lulumallfujairah",
          "ajmantourism","visitajman","ajmanmuseum","citycentreajman","ajmanchinamall","almanamall","ajmanmarina","alzorahbeachclub","ajman_corniche",
          "uaqtourism","visituaq","uaq_tourism","dreamlanduaq","dreamlandaquapark","uaqmarineclub","umm_al_quwain","uaqmall","kitebeachuaq","mangrovebeachuaq","barakogrilluaq"]:
    r = requests.get(f"{G}/{me}", params={"fields": f"business_discovery.username({h}){{username,name,followers_count,media_count,biography,website}}", "access_token": tok}, timeout=30).json()
    b = r.get("business_discovery")
    print("I|" + (f"{h}: {b.get('name')} | {b.get('followers_count')} | {b.get('media_count')} | {(b.get('biography') or '')[:80]!r} | {b.get('website')}" if b else f"{h}: -- {(r.get('error') or {}).get('message','')[:60]}"))
