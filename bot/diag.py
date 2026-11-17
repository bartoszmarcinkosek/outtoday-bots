"""Lista wszystkich wpisów 'pending' (eventy + oferty) do przeglądu."""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,price_text,is_free,gaps,source_name,official_url,category",
                       "status": "eq.pending", "order": "start_date", "limit": "2000"})
dl = db.get("deals", {"select": "id,title,venue,city,deal_type,price_text,days_of_week,start_time,end_time,valid_until,source_name,official_url",
                      "status": "eq.pending", "limit": "1000"})
print("EVENTS", len(ev)); print("DEALS", len(dl))
for e in ev:
    print("E|" + json.dumps(e, ensure_ascii=False))
for d in dl:
    print("D|" + json.dumps(d, ensure_ascii=False))
