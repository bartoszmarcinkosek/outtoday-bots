"""Wpisuje dane strony OutToday w App Store Connect przez API (NIE wysyła do przeglądu).

Uzupełnia: kategorie, nazwę/podtytuł/politykę prywatności, opis, słowa kluczowe, tekst promocyjny,
adresy, copyright, kategorię wiekową, dane dla recenzenta, zrzuty ekranu, cenę (darmowa)
i dostępność (wszystkie kraje poza Chinami). Każdy krok jest osobno – błąd jednego nie zatrzymuje reszty.
"""
import glob, hashlib, json, os, re, sys, time, traceback
import jwt, requests

APP_ID = os.environ["ASC_APP_ID"]
KEY = open(os.environ["EXPO_ASC_API_KEY_PATH"]).read()
SHOTS = sorted(glob.glob(os.path.join(os.environ["GITHUB_WORKSPACE"], "app/store/ios/ios-6.9-*.png")))
LOC = "en-US"

NAME = "OutToday: UAE Events & Deals"
SUBTITLE = "Things to do in Dubai & AD"
PROMO = ("What's on today across the UAE: concerts, festivals, brunches, happy hours, beaches and family days out, "
         "with prices and times from official pages.")
KEYWORDS = "dubai,abu dhabi,events,things to do,brunch,happy hour,ladies night,concerts,weekend,expat,sharjah"
DESCRIPTION = """OutToday shows what's on across the UAE today, this weekend and in the weeks ahead, all in one free app.

EVENTS
Concerts, comedy, theatre, festivals, exhibitions, sports, markets, runs and family days out in Dubai, Abu Dhabi, Al Ain, Sharjah, Ras Al Khaimah and the other emirates. Each event shows the date, start time, venue and ticket price, with a link to the official or ticket page.

PLACES
Beaches, parks, museums, attractions, souks, kids' activities and day trips, with opening hours and entry prices where the venue publishes them. Tap "Open now" to see what is open right now, or "Top 10" for the must-see places in each city.

DEALS
Weekly brunches, happy hours, ladies' nights, quiz nights, themed dinners and pool day passes, with the days, times and prices for each one.

MADE FOR EVERYDAY USE
• Filter by city, area, date, category, price and free entry
• See how far each place is from you
• Browse on the map
• Save favourites and add events to your calendar
• Share with friends and open directions in Google Maps or Waze
• Know an event we are missing? Suggest it in the app
• No account, no sign-up

HONEST INFORMATION
We collect details from official venue, organiser and ticketing pages and check them every day. If something looks wrong, tap "Report a problem" and we will fix it.

OutToday is independent and is not affiliated with the venues or organisers listed. Always check the official page before you go."""
NOTES = ("OutToday is a free guide to events, places and deals in the UAE. There is no login and no purchases. "
         "Content comes from official venue, organiser and ticketing pages and links back to them. Location is optional "
         "and used on-device only to show distance. Users can optionally suggest an event through a short form "
         "(email optional); suggestions are reviewed by us before anything is published.")
SITE = "https://outtodayapp.github.io"

results = []


def tok():
    return jwt.encode({"iss": os.environ["EXPO_ASC_ISSUER_ID"], "iat": int(time.time()), "exp": int(time.time()) + 900,
                       "aud": "appstoreconnect-v1"}, KEY, algorithm="ES256", headers={"kid": os.environ["EXPO_ASC_KEY_ID"]})


def api(method, path, **kw):
    url = path if path.startswith("http") else ("https://api.appstoreconnect.apple.com/" + (path if path.startswith("v") else "v1/" + path))
    r = requests.request(method, url, headers={"Authorization": f"Bearer {tok()}", "Content-Type": "application/json"}, timeout=120, **kw)
    if r.status_code >= 400:
        raise RuntimeError(f"{method} {path}: {r.status_code} {r.text[:800]}")
    return r.json() if r.text else {}


def step(name):
    def deco(fn):
        only = os.environ.get("ONLY", "").strip()
        if only and only.lower() not in name.lower():
            return fn
        try:
            fn()
            results.append(f"OK    {name}")
        except Exception as e:  # noqa: BLE001
            traceback.print_exc()
            results.append(f"BŁĄD  {name}: {str(e)[:300]}")
        return fn
    return deco


info = [i for i in api("GET", f"apps/{APP_ID}/appInfos")["data"]
        if i["attributes"].get("appStoreState") not in ("READY_FOR_SALE", "REMOVED_FROM_SALE")][0]
INFO_ID = info["id"]
ver = [v for v in api("GET", f"apps/{APP_ID}/appStoreVersions", params={"filter[platform]": "IOS"})["data"]
       if v["attributes"]["appStoreState"] in ("PREPARE_FOR_SUBMISSION", "DEVELOPER_REJECTED", "REJECTED", "METADATA_REJECTED")][0]
VER_ID = ver["id"]
print("appInfo", INFO_ID, "| version", VER_ID, ver["attributes"]["versionString"])


@step("kategorie (Lifestyle + Entertainment)")
def _():
    api("PATCH", f"appInfos/{INFO_ID}", json={"data": {"type": "appInfos", "id": INFO_ID, "relationships": {
        "primaryCategory": {"data": {"type": "appCategories", "id": "LIFESTYLE"}},
        "secondaryCategory": {"data": {"type": "appCategories", "id": "ENTERTAINMENT"}}}}})


@step("nazwa, podtytuł, polityka prywatności")
def _():
    locs = api("GET", f"appInfos/{INFO_ID}/appInfoLocalizations")["data"]
    attrs = {"name": NAME, "subtitle": SUBTITLE, "privacyPolicyUrl": f"{SITE}/privacy.html"}
    l = [x for x in locs if x["attributes"]["locale"] == LOC]
    if l:
        api("PATCH", f"appInfoLocalizations/{l[0]['id']}", json={"data": {"type": "appInfoLocalizations", "id": l[0]["id"], "attributes": attrs}})
    else:
        api("POST", "appInfoLocalizations", json={"data": {"type": "appInfoLocalizations", "attributes": {"locale": LOC, **attrs},
            "relationships": {"appInfo": {"data": {"type": "appInfos", "id": INFO_ID}}}}})


VLOC = {}


@step("opis, słowa kluczowe, tekst promocyjny, adresy")
def _():
    locs = api("GET", f"appStoreVersions/{VER_ID}/appStoreVersionLocalizations")["data"]
    attrs = {"description": DESCRIPTION, "keywords": KEYWORDS, "promotionalText": PROMO,
             "supportUrl": f"{SITE}/support.html", "marketingUrl": SITE}
    l = [x for x in locs if x["attributes"]["locale"] == LOC]
    if l:
        VLOC["id"] = l[0]["id"]
        api("PATCH", f"appStoreVersionLocalizations/{VLOC['id']}", json={"data": {"type": "appStoreVersionLocalizations", "id": VLOC["id"], "attributes": attrs}})
    else:
        VLOC["id"] = api("POST", "appStoreVersionLocalizations", json={"data": {"type": "appStoreVersionLocalizations",
            "attributes": {"locale": LOC, **attrs}, "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": VER_ID}}}}})["data"]["id"]


@step("copyright")
def _():
    api("PATCH", f"appStoreVersions/{VER_ID}", json={"data": {"type": "appStoreVersions", "id": VER_ID,
        "attributes": {"copyright": "2026 Julita Kosek", "releaseType": "MANUAL"}}})


@step("kategoria wiekowa (alkohol: często → 18+)")
def _():
    d = api("GET", f"appInfos/{INFO_ID}/ageRatingDeclaration")["data"]
    print("ageRating attrs:", json.dumps(d["attributes"]))
    out = {}
    for k, v in d["attributes"].items():
        if any(x in k.lower() for x in ("override", "korea", "grac", "url", "kidsageband", "classification")):
            continue
        if k == "alcoholTobaccoOrDrugUseOrReferences":
            out[k] = "FREQUENT_OR_INTENSE"
        elif isinstance(v, bool) or v is None and k[0:2] in ("is", "ha") or k in (
                "gambling", "unrestrictedWebAccess", "lootBox", "messagingAndChat", "userGeneratedContent", "advertising",
                "parentalControls", "ageAssurance", "healthOrWellnessTopics", "seventeenPlus"):
            out[k] = False
        elif v is None or isinstance(v, str):
            out[k] = "NONE"
    out["alcoholTobaccoOrDrugUseOrReferences"] = "FREQUENT_OR_INTENSE"
    # Apple nie mówi z góry, które pola są tak/nie, a które mają skalę – poprawiamy po komunikacie błędu.
    for _ in range(40):
        try:
            api("PATCH", f"ageRatingDeclarations/{d['id']}", json={"data": {"type": "ageRatingDeclarations", "id": d["id"], "attributes": out}})
            return
        except RuntimeError as e:
            m = re.search(r"attribute '(\w+)'\. Expected an? (\w+)", str(e))
            if not m:
                raise
            out[m.group(1)] = False if m.group(2) == "BOOLEAN" else "NONE"
            print("  poprawka typu:", m.group(1), "->", out[m.group(1)])
    raise RuntimeError("za dużo poprawek typów")


@step("dane dla recenzenta (kontakt + uwagi)")
def _():
    attrs = {"contactFirstName": "Julita", "contactLastName": "Kosek", "contactEmail": "outtodayapp.uae@gmail.com",
             "contactPhone": "+971585119871", "demoAccountRequired": False, "notes": NOTES}
    try:
        cur = api("GET", f"appStoreVersions/{VER_ID}/appStoreReviewDetail").get("data")
    except RuntimeError:
        cur = None
    if cur:
        api("PATCH", f"appStoreReviewDetails/{cur['id']}", json={"data": {"type": "appStoreReviewDetails", "id": cur["id"], "attributes": attrs}})
    else:
        api("POST", "appStoreReviewDetails", json={"data": {"type": "appStoreReviewDetails", "attributes": attrs,
            "relationships": {"appStoreVersion": {"data": {"type": "appStoreVersions", "id": VER_ID}}}}})


@step(f"zrzuty ekranu 6,9 cala ({len(SHOTS)} szt.)")
def _():
    sets = api("GET", f"appStoreVersionLocalizations/{VLOC['id']}/appScreenshotSets")["data"]
    err = None
    for dtype in ("APP_IPHONE_67", "APP_IPHONE_69"):
        s = [x for x in sets if x["attributes"]["screenshotDisplayType"] == dtype]
        try:
            sid = s[0]["id"] if s else api("POST", "appScreenshotSets", json={"data": {"type": "appScreenshotSets",
                "attributes": {"screenshotDisplayType": dtype},
                "relationships": {"appStoreVersionLocalization": {"data": {"type": "appStoreVersionLocalizations", "id": VLOC["id"]}}}}})["data"]["id"]
            break
        except RuntimeError as e:
            err = e
    else:
        raise err
    for old in api("GET", f"appScreenshotSets/{sid}/appScreenshots")["data"]:
        api("DELETE", f"appScreenshots/{old['id']}")
    for path in SHOTS:
        data = open(path, "rb").read()
        sh = api("POST", "appScreenshots", json={"data": {"type": "appScreenshots",
            "attributes": {"fileName": os.path.basename(path), "fileSize": len(data)},
            "relationships": {"appScreenshotSet": {"data": {"type": "appScreenshotSets", "id": sid}}}}})["data"]
        for op in sh["attributes"]["uploadOperations"]:
            part = data[op["offset"]:op["offset"] + op["length"]]
            h = {x["name"]: x["value"] for x in op.get("requestHeaders", [])}
            r = requests.request(op["method"], op["url"], headers=h, data=part, timeout=120)
            r.raise_for_status()
        api("PATCH", f"appScreenshots/{sh['id']}", json={"data": {"type": "appScreenshots", "id": sh["id"],
            "attributes": {"uploaded": True, "sourceFileChecksum": hashlib.md5(data).hexdigest()}}})
        print("  wysłano", os.path.basename(path))


@step("cena: darmowa")
def _():
    pts = api("GET", f"apps/{APP_ID}/appPricePoints", params={"filter[territory]": "USA", "limit": 200})["data"]
    free = [p for p in pts if float(p["attributes"]["customerPrice"]) == 0][0]
    api("POST", "appPriceSchedules", json={
        "data": {"type": "appPriceSchedules", "relationships": {
            "app": {"data": {"type": "apps", "id": APP_ID}},
            "baseTerritory": {"data": {"type": "territories", "id": "USA"}},
            "manualPrices": {"data": [{"type": "appPrices", "id": "${price0}"}]}}},
        "included": [{"type": "appPrices", "id": "${price0}", "attributes": {"startDate": None},
                      "relationships": {"appPricePoint": {"data": {"type": "appPricePoints", "id": free["id"]}}}}]})


@step("dostępność: wszystkie kraje poza Chinami")
def _():
    terr = []
    url = "territories?limit=200"
    while url:
        r = api("GET", url)
        terr += [t["id"] for t in r["data"]]
        url = r.get("links", {}).get("next")
    print("krajów:", len(terr))
    inc, refs = [], []
    for i, t in enumerate(terr):
        tid = f"${{t{i}}}"
        refs.append({"type": "territoryAvailabilities", "id": tid})
        inc.append({"type": "territoryAvailabilities", "id": tid, "attributes": {"available": t != "CHN"},
                    "relationships": {"territory": {"data": {"type": "territories", "id": t}}}})
    api("POST", "v2/appAvailabilities", json={"data": {"type": "appAvailabilities", "attributes": {"availableInNewTerritories": True},
        "relationships": {"app": {"data": {"type": "apps", "id": APP_ID}}, "territoryAvailabilities": {"data": refs}}},
        "included": inc})


print("\n==== WYNIK ====")
print("\n".join(results))
