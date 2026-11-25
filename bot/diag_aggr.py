"""Tylko odczyt: wydarzenia / oferty / miejsca z linkiem do agregatora w official_url (zakazane)."""
import os, sys, re, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
AG = re.compile(r"yalla|timeout|cobone|groupon|whatson\.ae|platinumlist\.net/guide|allevents|happydesertsafari|bayut|propertyfinder|thingstodo\.ae|rockhopping|wego|trip\.com|tripadvisor", re.I)
for t, name in (("events", "title"), ("deals", "title"), ("places", "name")):
    for r in db.get(t, {"select": f"id,{name},official_url,status", "official_url": "not.is.null", "limit": "20000"}):
        if AG.search(r["official_url"] or "") and r["status"] != "rejected":
            print(f"AG|{t}|{r['id']}|{r[name][:60]}|{r['official_url'][:90]}")
