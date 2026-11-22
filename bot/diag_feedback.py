"""Tylko odczyt: zgłoszenia od testerów (Feedback z ekranu About i Report z kart) z ostatnich 14 dni."""
import datetime as dt, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
since = (dt.date.today() - dt.timedelta(days=14)).isoformat()
rows = db.get("suggestions", {"select": "*", "created_at": f"gte.{since}", "order": "created_at.desc", "limit": "500"})
for r in rows:
    if (r.get("title") or "").startswith(("Feedback:", "Report:")):
        print(f"FB|{r.get('created_at','')[:16]}|{r.get('title')}|{(r.get('note') or '').replace(chr(10), ' / ')}|{r.get('contact') or ''}")
print(f"FB|razem: {len(rows)} zgłoszeń/propozycji od {since}")
