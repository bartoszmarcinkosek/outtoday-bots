"""Kontrola pokrycia (reguła 26.11.2026): ile zatwierdzonych ofert na miasto × dzień tygodnia × typ.
Luka = miasto/dzień, gdzie typ ma 0 ofert, a w większych miastach jest. Wynik: CV| (tabela), GAP| (luki do celowanego szukania)."""
import os, sys, collections, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
CITIES = ["Dubai", "Abu Dhabi", "Sharjah", "Al Ain", "Ras Al Khaimah", "Ajman", "Fujairah", "Umm Al Quwain"]
TYPES = ["ladies_night", "happy_hour", "brunch", "business_lunch", "quiz", "live_music", "day_pass"]
today = R.today_uae().isoformat()
c = collections.Counter()
types = collections.Counter()
for d in db.get("deals", {"select": "city,deal_type,days_of_week,valid_until", "status": "eq.approved", "limit": "10000"}):
    if d.get("valid_until") and d["valid_until"] < today:
        continue
    types[d.get("deal_type")] += 1
    for w in (d.get("days_of_week") or range(7)):
        c[(d.get("city"), w, d.get("deal_type"))] += 1
print("CV|types|" + ",".join(f"{k}:{v}" for k, v in types.most_common()))
for t in TYPES:
    for city in CITIES:
        row = [c[(city, w, t)] for w in range(7)]
        print(f"CV|{t}|{city}|" + " ".join(f"{DAYS[w]}:{row[w]}" for w in range(7)))
        # luka: typ istnieje w tym mieście w inne dni albo w ≥2 innych miastach tego dnia, a tu 0
        for w in range(7):
            if row[w] == 0 and sum(1 for o in CITIES if o != city and c[(o, w, t)] > 0) >= 2:
                print(f"GAP|{city}|{DAYS[w]}|{t}")
