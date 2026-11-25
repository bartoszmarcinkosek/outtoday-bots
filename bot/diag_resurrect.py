"""Tylko odczyt: pozycje dodane drugi raz przez ponowne stosowanie starych plików manual/ (po zmianie nazwy).
Dla każdego wpisu z kluczy "deals"/"places" w plikach manual/: wiersze w bazie o tej samej nazwie utworzone >36 h po dodaniu pliku."""
import os, sys, json, glob, subprocess, datetime as dt
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
def cdate(f):
    o = subprocess.run(["git", "log", "--diff-filter=A", "--format=%cI", "-1", "--", f], capture_output=True, text=True).stdout.strip()
    return dt.datetime.fromisoformat(o) if o else None
n = 0
for f in sorted(glob.glob("manual/*.json")):
    d = json.load(open(f)); cd = cdate(f)
    if not cd:
        continue
    lim = (cd + dt.timedelta(hours=36)).astimezone(dt.timezone.utc).isoformat()
    for x in d.get("deals", []):
        for r in db.get("deals", {"select": "id,title,venue,city,status,created_at", "title": f"eq.{x['title']}", "venue": f"eq.{x.get('venue')}", "created_at": f"gt.{lim}"}):
            n += 1; print(f"RS|deals|{r['id']}|{r['status']}|{r['created_at'][:16]}|{r['city']}|{r['venue']}|{r['title']}|{os.path.basename(f)}")
    for x in d.get("places", []):
        for r in db.get("places", {"select": "id,name,city,status,created_at", "name": f"eq.{x['name']}", "created_at": f"gt.{lim}"}):
            n += 1; print(f"RS|places|{r['id']}|{r['status']}|{r['created_at'][:16]}|{r['city']}||{r['name']}|{os.path.basename(f)}")
print(f"RT|resurrected {n}")
