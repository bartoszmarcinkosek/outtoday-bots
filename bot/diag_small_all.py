"""Tylko odczyt: WSZYSTKIE zatwierdzone pozycje z małych emiratów (pełny przegląd na życzenie)."""
import os, sys, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
C = ("Ras Al Khaimah", "Ajman", "Umm Al Quwain", "Fujairah", "Al Ain")
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date().isoformat()
def cell(x, k=170):
    return str(x if x is not None else "").replace("|", "/").replace("\n", " ")[:k]
for r in sorted(db.get("places", {"select": "*", "status": "eq.approved", "limit": "3000"}), key=lambda r: (r["city"] or "", r["category"] or "", r["name"] or "")):
    if r.get("city") in C:
        print("AP|" + "|".join(cell(r.get(k)) for k in ("id", "city", "category", "name", "area", "hours_text", "price_text", "is_free", "official_url", "lat", "lng", "description")))
for r in sorted(db.get("deals", {"select": "*", "status": "eq.approved", "limit": "3000"}), key=lambda r: (r["city"] or "", r["venue"] or "", r["deal_type"] or "")):
    if r.get("city") in C:
        print("AL|" + "|".join(cell(r.get(k)) for k in ("id", "city", "venue", "deal_type", "title", "days_of_week", "start_time", "end_time", "price_text", "valid_until", "official_url", "details")))
for r in sorted(db.get("events", {"select": "*", "status": "eq.approved", "limit": "5000"}), key=lambda r: (r["city"] or "", r["start_date"], r["title"] or "")):
    if r.get("city") in C and (r.get("end_date") or r["start_date"]) >= today:
        print("AE|" + "|".join(cell(r.get(k)) for k in ("id", "city", "start_date", "end_date", "start_time", "end_time", "category", "title", "venue", "price_text", "is_free", "official_url", "source_name", "description")))
