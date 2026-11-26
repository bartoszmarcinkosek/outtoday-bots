"""Tylko odczyt: nadchodzące wydarzenia oznaczone jako darmowe + sygnały, że jednak płatne (FR|...)."""
import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
t = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,city,title,price_text,price_min_aed,is_free,description,official_url,source_name,start_date,end_date",
                       "status": "eq.approved", "or": f"(end_date.gte.{t},and(end_date.is.null,start_date.gte.{t}))", "limit": "3000"})
PAID = re.compile(r"\baed\s?\d|\d+\s?aed|\bdhs?\b|ticket|tickets|book(ing)? (now|required)|per (person|child|adult)|fee|paid|charges? apply|entry fee|admission", re.I)
free = [e for e in ev if e.get("is_free") or (e.get("price_text") or "").strip().lower().startswith("free")]
sus = [e for e in free if PAID.search(f"{e.get('price_text') or ''} {e.get('description') or ''}") or (e.get("price_min_aed") or 0) > 0]
print(f"FS|upcoming {len(ev)}|free {len(free)}|suspicious {len(sus)}")
for e in sus:
    d = (e.get("description") or "").replace("|", "/").replace("\n", " ")
    m = PAID.search(f"{e.get('price_text') or ''} {d}")
    print(f"FR|{e['id']}|{e['city']}|{e['title']}|{e.get('price_text')}|{e.get('price_min_aed')}|{m.group(0) if m else ''}|{d[:220]}|{e.get('official_url') or ''}")
