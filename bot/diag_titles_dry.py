"""Tylko odczyt: lista tytułów, które fix_titles by poprawił (DRY)."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
import fix_titles
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ch = fix_titles.run(db, dry=True)
print(f"T|do poprawy: {len(ch)}")
for c in ch:
    print("T|" + c)
