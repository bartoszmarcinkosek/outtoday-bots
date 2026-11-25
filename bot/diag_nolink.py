"""Tylko odczyt: nadchodzące zatwierdzone wydarzenia bez official_url – źródło, dowód (link do posta), tekst ceny."""
import os, sys, json, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ti = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,title,venue,city,start_date,source_name,evidence,price_text,url,official_url",
    "status": "eq.approved", "or": f"(end_date.gte.{ti},and(end_date.is.null,start_date.gte.{ti}))", "limit": "8000"})
no = [e for e in ev if not e.get("official_url")]
print(f"NL|razem {len(ev)} bez linku {len(no)}")
c = collections.Counter((e.get("source_name") or "?")[:40] for e in no)
for k, n in c.most_common(25): print(f"NS|{n}|{k}")
for e in no:
    ev_ = e.get("evidence") or {}
    page = ev_.get("page") if isinstance(ev_, dict) else None
    print("NE|" + json.dumps({"id": e["id"], "d": e["start_date"], "t": e["title"][:60], "src": (e.get("source_name") or "")[:40], "page": (page or "")[:120], "url": (e.get("url") or "")[:120], "price": (e.get("price_text") or "")[:50]}, ensure_ascii=False))
