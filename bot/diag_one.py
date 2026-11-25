"""Tylko odczyt: jedna pozycja po id (ID=..., TABLE=places|events|deals) + ostatnie zgłoszenia z apki."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
i, t = os.environ.get("ID", "ee6fe91c-9cf0-4062-96b4-5bc9df5cfc70"), os.environ.get("TABLE", "places")
for r in db.get(t, {"select": "*", "id": f"eq.{i}"}):
    print("ON|" + json.dumps({k: v for k, v in r.items() if v not in (None, "", [])}, ensure_ascii=False)[:1500])
for tb in ("suggestions", "reports"):
    try:
        for r in db.get(tb, {"select": "*", "order": "created_at.desc", "limit": "6"}):
            print(f"RP|{tb}|" + json.dumps(r, ensure_ascii=False)[:500])
    except Exception as e:
        print(f"RP|{tb}|ERR {str(e)[:80]}")
