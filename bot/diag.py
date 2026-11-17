"""Jednorazowo 17.11: wpisy z Instagrama z przebiegu na starych zasadach.
- odrzuca złe (lista niżej),
- zatwierdza pełne (wszystkie szczegóły z cytatu), resztę zostawia do zatwierdzenia z dopiskiem czego brakuje."""
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = R.today_uae().isoformat()
now = dt.datetime.now(dt.timezone.utc).isoformat()

REJECT_EVENTS = ["The Mining Show", "Middle East Organic & Natural Products Expo", "International Apparel & Textile Fair",
                 "GeoWorld & Future FM", "HVACR World", "French Beginner Class for Teens",
                 "Introduction to French for children (ages 7–10)", "French course for adult complete beginners",
                 "Something special at Bâoli Dubai", "MOBLACK", "Festive Takeaway",
                 "Thursday carvery (smoked overnight, carved to order)", "Brunch de Folie"]
REJECT_DEALS = ["Winter Camp 2026", "Long Stay Offer", "Ultimate Pinoy Getaway"]

ev = db.get("events", {"select": "id,title,start_date,end_date,start_time,gaps,status,source_name",
                       "source_name": "like.OutToday Instagram bot*", "status": "eq.pending", "limit": "2000"})
ok = rej = left = 0
for e in ev:
    if e["title"] in REJECT_EVENTS or (e["start_date"] or "") < today:
        db.update("events", {"id": e["id"]}, {"status": "rejected"})
        rej += 1
        print(f"- odrzucony: {e['title']} {e['start_date']}")
        continue
    g = set(e.get("gaps") or [])
    full = not g or (g == {"start_time"} and e.get("end_date") and e["end_date"] > e["start_date"])
    if full:
        db.update("events", {"id": e["id"]}, {"status": "approved", "verified_at": now,
                                              "source_name": e["source_name"].replace("to verify", "official account")})
        ok += 1
        print(f"✓ zatwierdzony: {e['title']} {e['start_date']}")
    else:
        db.update("events", {"id": e["id"]}, {"source_name": e["source_name"].replace("to verify", "missing: " + ", ".join(sorted(g)))})
        left += 1
        print(f"? czeka (brak: {', '.join(sorted(g))}): {e['title']} {e['start_date']}")

dl = db.get("deals", {"select": "id,title,price_text,days_of_week,start_time,status,source_name",
                      "source_name": "like.OutToday Instagram bot*", "status": "eq.pending", "limit": "500"})
for d in dl:
    if d["title"] in REJECT_DEALS:
        db.update("deals", {"id": d["id"]}, {"status": "rejected"})
        rej += 1
        print(f"- oferta odrzucona: {d['title']}")
    elif d.get("price_text") and d.get("days_of_week") and d.get("start_time"):
        db.update("deals", {"id": d["id"]}, {"status": "approved"})
        ok += 1
        print(f"✓ oferta zatwierdzona: {d['title']}")
    else:
        left += 1
        print(f"? oferta czeka: {d['title']} (cena: {d.get('price_text') or '-'}, dni: {d.get('days_of_week') or '-'}, godz.: {d.get('start_time') or '-'})")
print(f"\nZatwierdzone: {ok}, odrzucone: {rej}, czeka na użytkownika: {left}")
