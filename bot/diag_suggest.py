"""Test tabeli suggestions: wstawienie kluczem publicznym (jak apka), brak odczytu, sprzątanie."""
import os, sys, requests
sys.path.insert(0, os.path.dirname(__file__))
import run as R
url = os.environ["SUPABASE_URL"].strip()
pub = "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"
h = {"apikey": pub, "Authorization": f"Bearer {pub}", "Content-Type": "application/json", "Prefer": "return=minimal"}
r = requests.post(f"{url}/rest/v1/suggestions", headers=h, json={"title": "TEST suggestion (delete)", "city": "Dubai"})
print("insert anon:", r.status_code, r.text[:200])
r = requests.get(f"{url}/rest/v1/suggestions?select=*", headers=h)
print("read anon (powinno być []):", r.status_code, r.text[:200])
r = requests.post(f"{url}/rest/v1/suggestions", headers=h, json={"title": "x", "city": "Dubai"})
print("za krótki tytuł (powinno 4xx):", r.status_code)
db = R.DB(url, os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("suggestions", {"select": "id,title", "title": "eq.TEST suggestion (delete)"})
print("widoczne dla bota:", len(rows))
for x in rows:
    requests.delete(f"{db.base}/suggestions", headers=db.h, params={"id": f"eq.{x['id']}"}, timeout=30)
print("posprzątane")
pl = db.get("places", {"select": "name,hours", "hours": "not.is.null", "limit": "3"})
print("places z hours:", pl)
