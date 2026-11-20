"""Tylko odczyt: szukanie wpisów po wzorcu (QE2, Hussam Al-Rassam)."""
import os, re, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,price_text,status,source_name,official_url",
                       "start_date": "gte.2026-11-20", "limit": "9000"})
rx = re.compile(r"QE2|Elf|Christmas Carol|ABBA|Rassam|Hameem|Aseel|حسام|أصيل|حكاية", re.I)
for e in ev:
    if rx.search((e["title"] or "") + " " + (e.get("venue") or "")):
        print("F|" + json.dumps(e, ensure_ascii=False))
