import os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
NL = re.compile(r"[Ѐ-ӿ؀-ۿऀ-ॿ]")
for tab, cols in (("events", "id,title,venue,status,source_name,description"), ("deals", "id,title,venue,status,details,price_text")):
    rows = db.get(tab, {"select": cols, "status": "in.(pending,approved)", "limit": "8000"})
    txt = lambda r: " ".join(str(r.get(k) or "") for k in ("title", "venue", "description", "details", "price_text"))
    bad = [r for r in rows if NL.search(txt(r))]
    print(f"T|{tab} {len(bad)}")
    for r in bad:
        print("T|" + json.dumps(r, ensure_ascii=False)[:400])
