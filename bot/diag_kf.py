"""Tylko odczyt: wszystko, co dotyczy wschodniego wybrzeża Szardży (Khor Fakkan, Kalba, Dibba Al Hisn) – każdy status."""
import os, sys, re, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
RX = re.compile(r"khor ?fakk?h?an|kalba|dibba|shees|rafisah|suhub|luluyah|zubarah|najd al maqsar|wadi al helo|al hefaiyah|khor kalba", re.I)
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date().isoformat()
def c(x, k=110): return str(x if x is not None else "").replace("|", "/").replace("\n", " ")[:k]
for r in db.get("places", {"select": "*", "limit": "3000"}):
    if RX.search(" ".join(str(r.get(k) or "") for k in ("name", "area", "city", "description"))):
        print("KP|" + "|".join(c(r.get(k)) for k in ("id", "status", "city", "category", "name", "area", "hours_text", "price_text", "official_url", "lat", "lng")))
for r in db.get("deals", {"select": "*", "limit": "5000"}):
    if RX.search(" ".join(str(r.get(k) or "") for k in ("title", "venue", "area", "city", "details"))):
        print("KL|" + "|".join(c(r.get(k)) for k in ("id", "status", "city", "venue", "deal_type", "title", "price_text", "official_url")))
for r in db.get("events", {"select": "*", "start_date": f"gte.2026-11-01", "limit": "8000"}):
    if (r.get("end_date") or r["start_date"]) >= today and RX.search(" ".join(str(r.get(k) or "") for k in ("title", "venue", "city", "description"))):
        print("KE|" + "|".join(c(r.get(k)) for k in ("id", "status", "city", "start_date", "end_date", "start_time", "category", "title", "venue", "price_text", "official_url")))
