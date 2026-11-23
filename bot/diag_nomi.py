import requests
UA = "OutToday-app/1.0 (UAE events app; contact outtodayapp.uae@gmail.com)"
for q in ["Al Ain Zoo, Al Ain", "Al Ain Oasis", "Al Ain Convention Centre"]:
    r = requests.get("https://nominatim.openstreetmap.org/search", params={"q": q, "format": "jsonv2", "limit": 1, "countrycodes": "ae"},
                     headers={"User-Agent": UA}, timeout=30)
    print("NM|", q, r.status_code, r.text[:150].replace("\n", " "))
