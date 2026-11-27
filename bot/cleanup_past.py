"""Czyszczenie bazy: usuwa wydarzenia zakończone ponad 30 dni temu (decyzja właściciela 27.11.2026:
„starsze niż miesiąc”). Apka i strona i tak ich nie pokazują; workflow robi wcześniej kopię zapasową."""
import datetime as dt, os, sys, requests
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
cut = (R.today_uae() - dt.timedelta(days=30)).isoformat()
old = db.get("events", {"select": "id,title,status,start_date,end_date", "or": f"(end_date.lt.{cut},and(end_date.is.null,start_date.lt.{cut}))", "limit": "20000"})
print(f"CL|zakończone przed {cut}: {len(old)}")
if len(old) > 5000:
    sys.exit("CL|za dużo naraz – przerwane dla bezpieczeństwa")
done = err = 0
for i in range(0, len(old), 100):
    ids = [e["id"] for e in old[i:i + 100]]
    r = requests.delete(f"{db.base}/events", headers=db.h, params={"id": f"in.({','.join(ids)})"}, timeout=60)
    if r.status_code < 400:
        done += len(ids)
    else:  # np. powiązania w innych tabelach – próbujemy pojedynczo
        for x in ids:
            r1 = requests.delete(f"{db.base}/events", headers=db.h, params={"id": f"eq.{x}"}, timeout=30)
            if r1.status_code < 400:
                done += 1
            else:
                err += 1
                print(f"CE|{x}|{r1.status_code} {r1.text[:150]}")
print(f"CL|usunięte {done} | błędy {err}")
