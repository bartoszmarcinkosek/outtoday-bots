import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from run import DB
from apply_changes import apply_safe_changes
db = DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
print("APPLIED", apply_safe_changes(db))
left = db.get("bot_changes", {"select": "table_name,field", "handled": "eq.false", "limit": "1000"})
print("LEFT", len(left), sorted({(x["table_name"], x["field"]) for x in left}))
