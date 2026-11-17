import os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,title,venue,city,start_date,source_name,official_url,description", "status": "eq.approved",
                       "or": f"(end_date.gte.{today},and(end_date.is.null,start_date.gte.{today}))", "limit": "5000"})
bad = [e for e in ev if re.search(r"[Ѐ-ӿ؀-ۿऀ-ॿ]", (e["title"] or "") + (e.get("venue") or ""))]
low = [e for e in ev if e.get("venue") and e["venue"] == e["venue"].lower() and re.search("[a-z]", e["venue"])]
print("NONLATIN", len(bad)); [print("N|" + json.dumps(e, ensure_ascii=False)[:500]) for e in bad]
print("LOWER", len(low)); [print("L|" + json.dumps({k: e[k] for k in ("id", "title", "venue")}, ensure_ascii=False)) for e in low]
