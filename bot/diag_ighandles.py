"""Tylko odczyt, bez AI i bez zapytań do Instagrama: z oficjalnych stron miejsc (audit/ig_sites.txt: miasto | miejsce | adres strony)
wyciąga linki do kont Instagram. Linie: IH|miasto|miejsce|strona|konto1,konto2  (puste = nie znaleziono / strona niedostępna)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
import ig_discover as D
import ig_seen
B = os.path.join(os.path.dirname(__file__), "..")
have = {x["username"].lower() for x in json.load(open(os.path.join(B, "sources", "instagram.json"), encoding="utf-8"))["accounts"]}
rej = ig_seen.load(hard_only=True)
rows = []
for l in open(os.path.join(B, "audit", "ig_sites.txt"), encoding="utf-8"):
    p = [x.strip() for x in l.split("|")]
    if not l.startswith("#") and len(p) >= 3 and p[2].startswith("http"):
        rows.append(p[:3])
with R.Browser() as br:
    for city, venue, url in rows:
        try:
            ok, _ = R.robots_allows(url)
            hs = sorted(D.handles_on(url, br)) if ok else []
            note = "" if ok else "robots"
        except Exception as e:
            hs, note = [], f"ERR {str(e)[:40]}"
        tag = ",".join(h + ("(mamy)" if h in have else "(odrzucone)" if h in rej else "") for h in hs)
        print(f"IH|{city}|{venue}|{url}|{tag or note}", flush=True)
