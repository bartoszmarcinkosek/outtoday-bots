"""Tylko odczyt: odczyt po zapisie – czy poprawki z plików manual/ dodanych w ostatnich HOURS godzinach (domyślnie 36) są w bazie.
Linie RB|plik|tabela|id|pole|oczekiwane|w bazie   oraz   RZ|podsumowanie. Nowszy plik zmieniający to samo pole ma pierwszeństwo."""
import os, sys, json, glob, subprocess, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
H = int(os.environ.get("HOURS", "36"))
def cdate(f):
    o = subprocess.run(["git", "log", "--format=%cI", "-1", "--", f], capture_output=True, text=True).stdout.strip()
    return dt.datetime.fromisoformat(o) if o else None
now = dt.datetime.now(dt.timezone.utc)
files = sorted(((cdate(f), f) for f in glob.glob("manual/*.json") if cdate(f)), key=lambda x: x[0])
files = [(d, f) for d, f in files if (now - d).total_seconds() < H * 3600 and (now - d).total_seconds() > 1200]   # pliki sprzed <20 min mogą się jeszcze stosować
want, rej = {}, {}
for d, f in files:   # od najstarszego: nowszy nadpisuje
    j = json.load(open(f))
    for key, t in (("update_event_ids", "events"), ("update_deal_ids", "deals"), ("update_place_ids", "places")):
        for u in j.get(key, []):
            for fld, v in (u.get("set") or {}).items():
                want[(t, u["id"], fld)] = (v, f)
    for key, t in (("reject_event_ids", "events"), ("reject_deal_ids", "deals"), ("reject_places", "places")):
        for i in j.get(key, []):
            rej[(t, i)] = f
def norm(v):
    if isinstance(v, str):
        v = v.strip()
        if len(v) in (5, 8) and v[2:3] == ":":
            return v[:5]
    return None if v in ("", [], None) else v
bad = 0
ids = {}
for (t, i, fld) in want:
    ids.setdefault(t, set()).add(i)
for (t, i) in rej:
    ids.setdefault(t, set()).add(i)
rows = {}
for t, s in ids.items():
    s = sorted(s)
    for k in range(0, len(s), 60):
        for r in db.get(t, {"select": "*", "id": "in.(" + ",".join(s[k:k + 60]) + ")"}):
            rows[(t, r["id"])] = r
for (t, i, fld), (v, f) in want.items():
    r = rows.get((t, i))
    if r is None:
        bad += 1; print(f"RB|{os.path.basename(f)}|{t}|{i}|{fld}|row not found|"); continue
    if fld not in r:
        continue
    if norm(r.get(fld)) != norm(v):
        bad += 1; print(f"RB|{os.path.basename(f)}|{t}|{i}|{fld}|{str(v)[:60]}|{str(r.get(fld))[:60]}")
for (t, i), f in rej.items():
    r = rows.get((t, i))
    if r is not None and r.get("status") != "rejected" and not any(k[0] == t and k[1] == i for k in want):
        bad += 1; print(f"RB|{os.path.basename(f)}|{t}|{i}|status|rejected|{r.get('status')}")
print(f"RZ|files checked {len(files)} | fields {len(want)} | rejections {len(rej)} | not in database {bad}")
