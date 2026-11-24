"""Tylko odczyt: miejsca i liczba wydarzen w malych emiratach + sprawdzenie kont IG."""
import os, sys, collections, requests
sys.path.insert(0, os.path.dirname(__file__))
import run as R
from instagram import ig_user_id, G
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
CITIES = ["Ajman", "Umm Al Quwain", "Fujairah", "Al Ain"]
cats = collections.Counter()
for r in db.get("places", {"select": "category", "limit": "2000"}):
    cats[r.get("category")] += 1
print("C|" + str(dict(cats)))
for c in CITIES:
    for r in db.get("places", {"select": "name,category,area,status,official_url", "city": f"eq.{c}", "limit": "300"}):
        print(f"P|{c}|{r['status']}|{r.get('category')}|{r['name']}|{r.get('area')}|{r.get('official_url')}")
    ev = db.get("events", {"select": "title,start_date,category", "city": f"eq.{c}", "status": "eq.approved", "end_date": "gte.2026-11-24", "limit": "400"})
    ev2 = db.get("events", {"select": "title,start_date,category", "city": f"eq.{c}", "status": "eq.approved", "end_date": "is.null", "start_date": "gte.2026-11-24", "limit": "400"})
    print(f"E|{c}|{len(ev)+len(ev2)}")
    for r in sorted(ev + ev2, key=lambda x: x["start_date"]):
        print(f"EV|{c}|{r['start_date']}|{r.get('category')}|{r['title']}")
tok = os.environ["IG_ACCESS_TOKEN"].strip(); me = ig_user_id(tok)
for h in os.environ.get("HANDLES", "alainmall,bawadimall,aljimimall,alainregion,visitalain,alainoasis,alqattaraartscentre,alainpalacemuseum,alainmuseum,hilifuncity,jebelhafeetdesertpark,alainfc,hazzabinzayedstadium,alainraceway,greenmubazzarah,remalmall,barari_outlet_mall,bararioutletmall,"
                        "ajmantourism,visitajman,ajmanmuseum,ajmanculture,alzorah,alzorahajman,oberoialzorah,theoberoibeachresortalzorah,ajmansaray,ajmanhotel,ajmanmarina,marsaajman,alzorahnaturereserve,questforadventure,ajmanstud,"
                        "uaqtourism,uaq_tourism,uaqgov,dreamlandaquapark,dreamlanduae,kitebeachcenter,kitebeachcenteruaq,vidabeachresortuaq,vidabeachresortummalquwain,pearlhoteluaq,casamikokouaq,mangrovebeachuaq,uaqmall,mallofuaq,"
                        "fujairahmall,lulumallfujairah,fujairahfort,lemeridienalaqah,royalmfujairah,addressbeachresortfujairah,addressfujairah,minielclub,fujairahobserver,fujairahgov,fujairahadventures,alaqahbeach,snoopyisland,dibbabay,fujairahcreativecity,fujairahexhibitioncentre,wadiwurayah").split(","):
    r = requests.get(f"{G}/{me}", params={"fields": f"business_discovery.username({h}){{username,name,followers_count,media_count,biography,website,media.limit(1){{timestamp}}}}", "access_token": tok}, timeout=30).json()
    b = r.get("business_discovery")
    if b:
        last = ((b.get("media") or {}).get("data") or [{}])[0].get("timestamp", "")[:10]
        print(f"I|{h}|{b.get('name')}|{b.get('followers_count')}|{b.get('media_count')}|{last}|{(b.get('biography') or '')[:90]!r}|{b.get('website')}")
    else:
        print(f"I|{h}|--")
