"""Tylko odczyt: linki prowadzące do artykułów-list („Top 20 things to do”, /blog/), a nie do strony tej pozycji (LL|kind|id|city|title|url)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
BAD = re.compile(r"/blog/|/blogs?/?$|/articles?/|top-?\d+|things-to-do|best-.*-in-|/guides?/|\?p=\d+", re.I)
t = R.today_uae().isoformat()
for table, name in (("events", "title"), ("deals", "title"), ("places", "name")):
    q = {"select": f"id,city,{name},official_url", "status": "eq.approved", "official_url": "not.is.null", "limit": "5000"}
    if table == "events": q["or"] = f"(end_date.gte.{t},and(end_date.is.null,start_date.gte.{t}))"
    for r in db.get(table, q):
        u = r.get("official_url") or ""
        if BAD.search(u):
            print(f"LL|{table}|{r['id']}|{r['city']}|{r[name]}|{u}")
