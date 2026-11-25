"""Pomocnik lokalny: zapisuje wynik diag_igcheck.

python bot/ig_apply.py <plik z liniami IG|miasto|konto|wynik...> [--skip konto1,konto2]
- OK, >= 1000 obserwujących i ostatni post nie starszy niż pół roku -> sources/instagram.json
- nie istnieje / martwe / za małe / --skip (odrzucone ręcznie) -> audit/ig_rejected.txt (nie sprawdzamy drugi raz)
- nie sprawdzone przez limit Instagrama -> zostają w audit/ig_candidates.txt
"""
import collections, datetime as dt, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import ig_seen
B = os.path.join(os.path.dirname(__file__), "..")
CF, JF = os.path.join(B, "audit", "ig_candidates.txt"), os.path.join(B, "sources", "instagram.json")
skip = set()
if "--skip" in sys.argv:
    skip = {x.strip().lower() for x in sys.argv[sys.argv.index("--skip") + 1].split(",")}
lines = [l.rstrip("\n") for l in open(CF, encoding="utf-8")]
ven = {}
for l in lines:
    p = [x.strip() for x in l.split("|")]
    if not l.startswith("#") and len(p) > 1:
        ven[p[1].lower()] = p[2] if len(p) > 2 else "-"
j = json.load(open(JF, encoding="utf-8")); have = {x["username"].lower() for x in j["accounts"]}
done, add, rej = set(), [], []
for l in open(sys.argv[1], encoding="utf-8"):
    p = l.rstrip("\n").split("|")
    if len(p) < 4 or p[0] != "IG":
        continue
    city, u, res = p[1], p[2], p[3]
    if "request limit" in res or res.startswith("ERR"):
        continue
    done.add(u.lower())
    if res.startswith("JUŻ"):
        continue
    if res.startswith("BRAK"):
        rej.append((u, "nie istnieje pod tą nazwą")); continue
    fol = int(re.search(r"\d+", res).group()); last = (p[4] if len(p) > 4 else "").replace("ost. post", "").strip()
    try:
        age = (dt.date.today() - dt.date.fromisoformat(last)).days
    except Exception:
        age = 9999
    if u.lower() in skip:
        rej.append((u, "odrzucone ręcznie (inne miejsce / nie pasuje)"))
    elif fol < 1000:
        rej.append((u, f"za mało obserwujących ({fol})"))
    elif age > 183:
        rej.append((u, f"martwe konto (ostatni post {last})"))
    elif u.lower() not in have:
        d = {"username": u, "city": city}
        if ven.get(u.lower(), "-") not in ("", "-"):
            d["venue"] = ven[u.lower()]
        add.append(d); have.add(u.lower())
j["accounts"].extend(add)
json.dump(j, open(JF, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
n = ig_seen.add(rej)
rest = [l for l in lines if l.startswith("#") or (len(l.split("|")) > 1 and l.split("|")[1].strip().lower() not in done)]
open(CF, "w", encoding="utf-8").write("\n".join(rest) + "\n")
print("dodane", len(add), dict(collections.Counter(x["city"] for x in add)), [x["username"] for x in add])
print("odrzucone (zapisane)", n, "| razem kont", len(j["accounts"]), "| zostało do sprawdzenia", len([l for l in rest if not l.startswith("#")]))
