"""Tylko odczyt: stan źródeł. SS| ocena źródeł (zatwierdzone/odrzucone/czekające), SB| źródła blokowane lub puste w ostatnich przebiegach."""
import os, sys, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
sc = collections.defaultdict(collections.Counter)
for t in ("events", "deals"):
    for r in db.get(t, {"select": "source_name,status", "limit": "40000"}):
        n = r.get("source_name") or ""
        m = re.search(r"@([\w.]+)", n)
        key = f"ig:{m.group(1).lower()}" if ("Instagram" in n and m) else n
        sc[key][r.get("status") or "?"] += 1
for k, c in sorted(sc.items(), key=lambda x: -x[1]["rejected"]):
    tot = sum(c.values())
    if c["rejected"] >= 2:
        print(f"SS|{k[:60]}|total {tot}|approved {c['approved']}|rejected {c['rejected']}|pending {c['pending']}|{round(100*c['rejected']/tot)}%")
print(f"SA|keys {len(sc)}|statuses {dict(sum((c for c in sc.values()), collections.Counter()))}")
runs = db.get("bot_runs", {"select": "finished_at,summary", "order": "finished_at.desc", "limit": "12"})
st = collections.defaultdict(list)
for r in runs:
    for s in ((r.get("summary") or {}).get("sources") or []):
        st[(s.get("source"), s.get("url"))].append(s.get("status") or "")
for (n, u), ss in sorted(st.items()):
    real = [x for x in ss if x and not x.startswith("sprawdzane co")]
    if real and all(("ZABRANIA" in x or "pusta lub błąd" in x or "błąd pobierania" in x or "nie odpowiada" in x or "błąd serwera" in x) for x in real):
        print(f"SB|{n}|{u}|{real[0][:60]}|{len(real)}x")
print(f"SR|runs {len(runs)}|source urls {len(st)}")
for k in sorted(db.probation()):
    print(f"SP|{k}")
