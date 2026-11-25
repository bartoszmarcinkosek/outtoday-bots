"""Tylko odczyt: dziury w ofercie na najbliższe 14 dni. Linie:
GD|miasto|dzień po dniu: liczba wydarzeń (+ ofert ważnych tego dnia tygodnia)   – dni z zerem wydarzeń oznaczone !
GC|miasto|kategoria=liczba wydarzeń w 14 dni ...     GP|miasto|kategoria=liczba miejsc ...    GZ|podsumowanie"""
import os, sys, collections, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
C = ["Abu Dhabi", "Al Ain", "Dubai", "Sharjah", "Ajman", "Umm Al Quwain", "Ras Al Khaimah", "Fujairah"]
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date()
days = [today + dt.timedelta(days=i) for i in range(14)]
ev = db.get("events", {"select": "city,category,start_date,end_date", "status": "eq.approved", "start_date": f"lte.{days[-1].isoformat()}", "limit": "5000"})
dl = db.get("deals", {"select": "city,deal_type,days_of_week", "status": "eq.approved", "limit": "5000"})
pl = db.get("places", {"select": "city,category", "status": "eq.approved", "limit": "5000"})
cats = sorted({r.get("category") or "?" for r in ev})
empty = []
for c in C:
    cnt, cc = [], collections.Counter()
    for d in days:
        ds = d.isoformat()
        # długie wystawy/sezony (ponad 21 dni) nie liczą się jako „coś na dziś"
        n = sum(1 for r in ev if r.get("city") == c and r["start_date"] <= ds <= (r.get("end_date") or r["start_date"])
                and (dt.date.fromisoformat(r.get("end_date") or r["start_date"]) - dt.date.fromisoformat(r["start_date"])).days <= 21)
        dow = (d.weekday() + 1) % 7   # 0 = niedziela, jak w apce
        m = sum(1 for r in dl if r.get("city") == c and (not r.get("days_of_week") or dow in r["days_of_week"]))
        cnt.append(f"{d.strftime('%a %d')}:{n}{'!' if n == 0 else ''}+{m}")
        if n == 0:
            empty.append((c, ds))
    for r in ev:
        if r.get("city") == c and (r.get("end_date") or r["start_date"]) >= today.isoformat():
            cc[r.get("category") or "?"] += 1
    print(f"GD|{c}|" + " ".join(cnt))
    print(f"GC|{c}|" + " ".join(f"{k}={cc.get(k, 0)}" for k in cats))
    pc = collections.Counter(r.get("category") or "?" for r in pl if r.get("city") == c)
    print(f"GP|{c}|" + " ".join(f"{k}={v}" for k, v in sorted(pc.items())) + f" | deals={sum(1 for r in dl if r.get('city') == c)}")
byc = collections.Counter(c for c, _ in empty)
print("GZ|days without any event in the next 14: " + ", ".join(f"{c} {n}" for c, n in byc.most_common()) if empty else "GZ|every emirate has an event every day")
