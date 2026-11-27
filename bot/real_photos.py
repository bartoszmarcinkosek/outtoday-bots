"""Prawdziwe zdjęcia miejsc (Pexels / Wikimedia Commons) do apki – decyzja właściciela 27.11.2026.
Czyta photos/real_fetch.txt: linie `<nazwa np. lm_etihad_arena-3> | <adres obrazka> | <podpis autora/licencji albo -> | <kadr: center|left|right|0.35>`.
Pobiera, przycina do 2:3 (pion), zapisuje app/assets/photos/<nazwa>.jpg (240x360) i full/<nazwa>.jpg (400x600),
dopisuje podpis do photos/credits.json, czyści przetworzone linie, odświeża photos.gen.ts. Wypisuje RP|ok|nazwa|rozmiar albo RP|err|nazwa|powód."""
import io, json, os, subprocess, sys
import requests
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
LIST = os.path.join(ROOT, "photos", "real_fetch.txt")
CRED = os.path.join(ROOT, "photos", "credits.json")
UA = {"User-Agent": "OutTodayBot/1.0 (https://outtoday.ae; photos for an events app)"}
cred = json.load(open(CRED)) if os.path.exists(CRED) else {}
keep, done = [], 0
for line in open(LIST, encoding="utf-8").read().splitlines() if os.path.exists(LIST) else []:
    if not line.strip() or line.startswith("#"):
        keep.append(line); continue
    p = [x.strip() for x in line.split("|")]
    name, url = p[0], p[1]
    credit = p[2] if len(p) > 2 and p[2] not in ("", "-") else None
    crop = p[3] if len(p) > 3 and p[3] else "center"
    try:
        import time
        for _ in range(4):
            r = requests.get(url, headers=UA, timeout=60)
            if r.ok and r.headers.get("content-type", "").startswith("image"):
                break
            time.sleep(5)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGB"); w, h = im.size
        if w / h > 2 / 3:
            nw = round(h * 2 / 3)
            pos = {"center": 0.5, "left": 0.0, "right": 1.0}.get(crop)
            pos = float(crop) if pos is None else pos
            x = round((w - nw) * pos); im = im.crop((x, 0, x + nw, h))
        else:
            nh = round(w * 3 / 2); y = (h - nh) // 2; im = im.crop((0, y, w, y + nh))
        im.resize((400, 600), Image.LANCZOS).save(os.path.join(ROOT, "app/assets/photos/full", name + ".jpg"), quality=85, optimize=True)
        im.resize((240, 360), Image.LANCZOS).save(os.path.join(ROOT, "app/assets/photos", name + ".jpg"), quality=85, optimize=True)
        if credit:
            cred[name] = credit
        else:
            cred.pop(name, None)
        done += 1; print(f"RP|ok|{name}|{w}x{h}")
    except Exception as e:  # noqa: BLE001
        keep.append(line); print(f"RP|err|{name}|{e}")
json.dump(cred, open(CRED, "w"), ensure_ascii=False, indent=1)
open(LIST, "w", encoding="utf-8").write("\n".join(keep) + ("\n" if keep else ""))
subprocess.run([sys.executable, os.path.join(ROOT, "app/scripts/gen-photos.py")], check=True)
print(f"RP|SUMMARY|added {done}")
