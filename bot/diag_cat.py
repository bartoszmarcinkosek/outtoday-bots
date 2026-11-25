"""Tylko odczyt: zatwierdzone wydarzenia w kategorii CAT (domyślnie comedy)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for r in db.get("events", {"select": "id,title,city,start_date,category", "status": "eq.approved", "category": f"eq.{os.environ.get('CAT', 'comedy')}", "limit": "500"}):
    print(f"CT|{r['id']}|{r['city']}|{r['start_date']}|{r['title']}")
