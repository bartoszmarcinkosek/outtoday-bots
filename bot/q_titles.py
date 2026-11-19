import os, run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for e in db.get("deals", {"select": "id,title,venue,city,deal_type,status,price_text,details", "title": "ilike.*Sangria*", "limit": "10"}):
    print("D |", e)
