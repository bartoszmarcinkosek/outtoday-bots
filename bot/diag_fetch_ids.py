"""Tylko odczyt, bez AI: otwiera stronę źródłową (official_url) pozycji o id z audit/fetch_ids.txt prawdziwą przeglądarką,
tak jak boty (szanuje robots.txt). Do nocnych kontroli – zamiast WebFetch, który w zadaniach zaplanowanych bywa niedostępny.
Linie: FI|tabela|id|miasto|tytuł|miejsce|dni|godz.|cena|ważne do|url  FS|id|status HTTP|adres końcowy  FT|id|tekst strony (do ~6000 znaków)."""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ids = [l.split()[0] for l in open(os.path.join(os.path.dirname(__file__), "..", "audit", "fetch_ids.txt")) if l.strip() and not l.startswith("#")][:40]
rows = []
for t, cols in (("deals", "id,city,title,venue,days_of_week,start_time,end_time,price_text,valid_until,official_url,details"),
                ("events", "id,city,title,venue,start_date,start_time,end_time,price_text,end_date,official_url,description"),
                ("places", "id,city,name,area,hours_text,price_text,official_url,description")):
    for r in db.get(t, {"select": cols, "id": f"in.({','.join(ids)})"}):
        rows.append((t, r))
with R.Browser() as br:
    for t, r in rows:
        print("FI|" + "|".join([t] + [str(v if v is not None else "") .replace("|", "/")[:300] for v in r.values()]))
        u = r.get("official_url")
        if not u:
            print(f"FS|{r['id']}|brak linku|"); continue
        ok, why = R.robots_allows(u)
        if not ok:
            print(f"FS|{r['id']}|{why}|{u}"); continue
        try:
            p = br.fetch(u)
            print(f"FS|{r['id']}|{p['status']}|{p.get('final_url', u)}")
            txt = re.sub(r"\s+", " ", p.get("full_text") or p.get("text") or "")
            for i in range(0, min(len(txt), 6000), 500):
                print(f"FT|{r['id']}|{txt[i:i+500]}")
        except Exception as e:
            print(f"FS|{r['id']}|błąd {type(e).__name__}|{u}")
