"""Tylko odczyt: szukaj eventów po słowach z argumentu KW (env), z source i url."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
KW = ["cats the musical", "chocolate factory", "riverdance", "tarkan", "aquafit", "face aux murs", "jewels of emirates", "bootcamp", "youssou", "little christmas makers", "phantom", "mamma mia", "lion king", "wicked"]
for k in KW:
    for r in db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,status,source,official_url", "title": f"ilike.*{k}*",
                               "start_date": "gte.2026-11-01", "status": "eq.approved", "limit": "40"}):
        print(f"F5|{r['start_date']}..{r.get('end_date') or ''}|{r.get('start_time') or ''}|{r['title']}|{r.get('venue')}|{r['city']}|{r.get('source')}|{r.get('official_url')}|{r['id']}")
