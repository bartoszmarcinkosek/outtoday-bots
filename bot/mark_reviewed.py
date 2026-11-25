"""Pomocnik zadań kontroli (uruchamiany lokalnie w klonie repo, nie łączy się z bazą):
python3 bot/mark_reviewed.py audit/reviewed.json id1 id2 ...   (albo id-ki na wejściu standardowym, po jednym w linii)
Zapisuje dzisiejszą datę (Dubaj) przy podanych id; wpisy starsze niż 90 dni usuwa."""
import sys, json, os, datetime as dt
path = sys.argv[1]
ids = sys.argv[2:] or [l.strip() for l in sys.stdin if l.strip()]
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date()
try:
    d = json.load(open(path))
except Exception:
    d = {}
for i in ids:
    d[i] = today.isoformat()
old = (today - dt.timedelta(days=90)).isoformat()
d = {k: v for k, v in d.items() if v >= old}
json.dump(d, open(path, "w"), indent=0, sort_keys=True)
print(f"{os.path.basename(path)}: marked {len(ids)}, total {len(d)}")
