"""Tylko odczyt: marki lokali (pierwszy człon nazwy miejsca) z ofert i miejsc, z listą miast. Do szukania siostrzanych lokali w innych emiratach."""
import os, sys, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
CITY = re.compile(r"\b(dubai|abu dhabi|sharjah|ajman|fujairah|rak|ras al khaimah|umm al quwain|uaq|al ain|the palm|jbr|marina|yas|saadiyat)\b", re.I)
def brand(v):
    b = (v or "").split(",")[0].split(" at ")[0].split(" - ")[0].split(" – ")[0].split("(")[0]
    b = CITY.sub("", b).strip(" -–'’")
    return re.sub(r"\s+", " ", b).lower()
m = collections.defaultdict(lambda: collections.defaultdict(int))
for r in db.get("deals", {"select": "venue,city", "status": "eq.approved", "limit": "5000"}):
    if r.get("venue"): m[brand(r["venue"])][r["city"]] += 1
for r in db.get("places", {"select": "name,city", "status": "eq.approved", "limit": "5000"}):
    if r.get("name"): m[brand(r["name"])][r["city"]] += 1
for b, c in sorted(m.items(), key=lambda x: -sum(x[1].values())):
    if len(b) > 2:
        print("BR|" + b + "|" + ",".join(f"{k}:{v}" for k, v in sorted(c.items())))
