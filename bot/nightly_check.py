"""Nocna kontrola danych BEZ AI (koszt 0 USD): niedziałające linki i oczywiste duplikaty.
Nic nie zmienia w danych – zapisuje raport w bot_runs (summary.kind = "nightly_check"), a poranny e-mail go pokazuje.
Linki: każdej nocy sprawdza część (ok. 1/7), więc każdy link jest sprawdzany mniej więcej raz w tygodniu."""
import datetime as dt
import hashlib
import os
import re
import sys
import time
from urllib.parse import urlparse

import requests

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
today = dt.datetime.now(dt.timezone(dt.timedelta(hours=4))).date()
day_slot = today.toordinal() % 7

ev = [e for e in db.get("events", {"select": "id,title,start_date,end_date,city,venue,official_url,url", "status": "eq.approved",
                                   "start_date": f"gte.{(today - dt.timedelta(days=120)).isoformat()}", "limit": "8000"})
      if (e.get("end_date") or e["start_date"]) >= today.isoformat()]
pl = db.get("places", {"select": "id,name,city,official_url", "status": "eq.approved", "limit": "5000"})
dl = db.get("deals", {"select": "id,title,venue,city,official_url", "status": "eq.approved", "limit": "5000"})


def key(s: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", R.norm(s or "")).strip()


# ---- duplikaty (ten sam tytuł + ten sam dzień + to samo miasto; miejsca: ta sama nazwa + miasto)
dupes = []
groups: dict[tuple, list] = {}
for e in ev:
    groups.setdefault(("event", key(e["title"]), e["start_date"], e["city"]), []).append(e)
for p in pl:
    groups.setdefault(("place", key(p["name"]), "", p["city"]), []).append(p)
for d in dl:
    groups.setdefault(("deal", key(d["title"]), key(d.get("venue")), d["city"]), []).append(d)
for (kind, _, _, city), rows in groups.items():
    if len(rows) > 1:
        dupes.append({"kind": kind, "title": rows[0].get("title") or rows[0].get("name"), "city": city,
                      "date": rows[0].get("start_date"), "ids": [r["id"] for r in rows]})

# ---- linki (404/410/brak domeny = martwy; 403/429 = strona blokuje automaty, pomijamy)
links: dict[str, list] = {}
for kind, rows in (("event", ev), ("place", pl), ("deal", dl)):
    for r in rows:
        u = r.get("official_url") or r.get("url")
        if u and u.startswith("http"):
            links.setdefault(u, []).append({"kind": kind, "id": r["id"], "title": r.get("title") or r.get("name"), "city": r.get("city")})
todo = [u for u in links if int(hashlib.md5(u.encode()).hexdigest(), 16) % 7 == day_slot]
dead = []
UA = {"User-Agent": "Mozilla/5.0 (compatible; OutTodayBot/1.0; +https://outtodayapp.github.io)"}
for u in todo:
    ok, _ = R.robots_allows(u)
    if not ok:
        continue
    why = None
    try:
        r = requests.get(u, headers=UA, timeout=15, allow_redirects=True)
        if r.status_code in (404, 410):
            why = f"HTTP {r.status_code}"
    except requests.exceptions.ConnectionError as ex:
        if "Name or service not known" in str(ex) or "NameResolutionError" in str(ex):
            why = "domena nie istnieje"
    except requests.RequestException:
        pass  # chwilowy błąd sieci – nie zgłaszamy
    if why:
        for x in links[u]:
            dead.append({**x, "url": u, "why": why})
    time.sleep(0.5)

print(f"L|eventy {len(ev)}, miejsca {len(pl)}, oferty {len(dl)} | duplikaty: {len(dupes)} | linki sprawdzone {len(todo)}/{len(links)}, martwe: {len(dead)}")
for d in dupes[:50]:
    print("L|DUP", d["kind"], d["date"] or "", d["city"], d["title"][:60], len(d["ids"]))
for d in dead[:50]:
    print("L|DEAD", d["kind"], d["title"][:50], urlparse(d["url"]).netloc, d["why"])
# ---- poprawki (zgoda Bartosza 19.11: "jak coś znajdziesz to poprawiaj")
# duplikat: zostaje wpis z największą liczbą wypełnionych pól, reszta -> rejected
# martwy link: event zostaje, link usunięty; miejsce/oferta -> pending (ukryte), bo strona zniknęła = oferta mogła się skończyć
fixed = []
if not os.environ.get("DRY"):
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    table_of = {"event": "events", "place": "places", "deal": "deals"}
    pool = {("event", r["id"]): r for r in ev} | {("place", r["id"]): r for r in pl} | {("deal", r["id"]): r for r in dl}
    for d in dupes:
        rows = sorted((pool[(d["kind"], i)] for i in d["ids"]), key=lambda r: -sum(1 for v in r.values() if v))
        for r in rows[1:]:
            db.update(table_of[d["kind"]], {"id": r["id"]}, {"status": "rejected"})
            fixed.append(f"duplikat usunięty: {d['title']}")
    for d in dead:
        if d["kind"] == "event":
            row = pool[("event", d["id"])]
            fix = {"official_url": None} if row.get("official_url") == d["url"] else {"url": None}
            db.update("events", {"id": d["id"]}, {**fix, "updated_at": now})
            fixed.append(f"martwy link usunięty: {d['title']}")
        else:
            db.update(table_of[d["kind"]], {"id": d["id"]}, {"status": "pending"})
            fixed.append(f"ukryte do sprawdzenia (strona zniknęła): {d['title']}")
    for f in fixed:
        print("L|FIX", f)
if not os.environ.get("DRY"):
    db.insert("bot_runs", {"dry_run": False, "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                           "summary": {"kind": "nightly_check", "report": {"dupes": dupes[:60], "dead": dead[:60],
                                                                          "checked": len(todo), "links": len(links), "fixed": fixed[:80]}}})
