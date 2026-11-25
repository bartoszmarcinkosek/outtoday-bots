"""Tylko odczyt: oferty, w których dni tygodnia zapisane w bazie (0 = niedziela ... 6 = sobota, jak w apce)
nie zgadzają się z dniami nazwanymi w tytule/opisie/cenie. Linie DD|id|miasto|miejsce|tytuł|dni w bazie|dni w tekście|fragment"""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
N = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
FULL = {"sunday": 0, "monday": 1, "tuesday": 2, "wednesday": 3, "thursday": 4, "friday": 5, "saturday": 6}
def named(t):
    t = (t or "").lower()
    out = set()
    for w, i in FULL.items():
        if re.search(rf"\b{w}s?\b", t):
            out.add(i)
    for a, b in re.findall(r"\b(sun|mon|tue|wed|thu|fri|sat)[a-z]*\s*(?:-|–|to|till|until|through)\s*(sun|mon|tue|wed|thu|fri|sat)[a-z]*\b", t):
        i, j = N.index(a), N.index(b)
        k = i
        while True:
            out.add(k)
            if k == j:
                break
            k = (k + 1) % 7
    if re.search(r"\bweekdays?\b", t):
        out |= {1, 2, 3, 4}
    if re.search(r"\b(daily|every ?day|all week|7 days)\b", t):
        out |= set(range(7))
    return out
rows = db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,details,price_text", "status": "eq.approved", "limit": "3000"})
bad = nodays = 0
for r in rows:
    days = set(r.get("days_of_week") or [])
    tt = named(r.get("title"))
    al = tt | named(r.get("details")) | named(r.get("price_text"))
    if not days:
        if al and r.get("deal_type") != "staycation":
            nodays += 1
            print(f"DE|{r['id']}|{r['city']}|{(r['venue'] or '')[:40]}|{(r['title'] or '')[:60]}|[]|{sorted(al)}|{(r.get('details') or '')[:140]}")
        continue
    # błąd: tytuł nazywa dzień, którego nie ma w bazie; albo tekst nazywa dni i żaden nie pokrywa się z bazą
    if (tt and not tt <= days) or (al and not (al & days)):
        bad += 1
        print(f"DD|{r['id']}|{r['city']}|{(r['venue'] or '')[:40]}|{(r['title'] or '')[:60]}|{sorted(days)}|{sorted(al)}|{(r.get('details') or '')[:140]}")
print(f"DS|deals {len(rows)} | day mismatch {bad} | days named in text but none stored {nodays}")
