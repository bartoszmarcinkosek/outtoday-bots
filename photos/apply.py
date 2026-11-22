"""Wrzuca pobrane z Canvy zdjęcia do apki (bez AI, koszt 0).
Użycie: python3 photos/apply.py <katalog_z_png>
W katalogu pliki <nazwa>.png (np. brunch-4.png) – strona 400x600 z Canvy.
Tworzy app/assets/photos/<nazwa>.jpg (240x360, karta) i app/assets/photos/full/<nazwa>.jpg (400x600, szczegóły),
dopisuje nazwy do "in_app" w photos/canva_map.json i odświeża app/src/photos.gen.ts."""
import json
import os
import subprocess
import sys

from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
src = sys.argv[1]
mp = os.path.join(ROOT, "photos", "canva_map.json")
m = json.load(open(mp))
added = []
for f in sorted(os.listdir(src)):
    if not f.endswith(".png"):
        continue
    name = f[:-4]
    im = Image.open(os.path.join(src, f)).convert("RGB")
    w, h = im.size
    # przytnij do 2:3 (środek), gdyby Canva oddała inny rozmiar
    if abs(w / h - 2 / 3) > 0.01:
        if w / h > 2 / 3:
            nw = round(h * 2 / 3); im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
        else:
            nh = round(w * 3 / 2); im = im.crop((0, (h - nh) // 2, w, (h - nh) // 2 + nh))
    im.resize((400, 600), Image.LANCZOS).save(os.path.join(ROOT, "app/assets/photos/full", name + ".jpg"), quality=85, optimize=True)
    im.resize((240, 360), Image.LANCZOS).save(os.path.join(ROOT, "app/assets/photos", name + ".jpg"), quality=85, optimize=True)
    added.append(name)
m["in_app"] = sorted(set(m.get("in_app", [])) | set(added))
json.dump(m, open(mp, "w"), ensure_ascii=False, indent=1)
subprocess.run([sys.executable, os.path.join(ROOT, "app/scripts/gen-photos.py")], check=True)
print(f"dodane do apki: {len(added)}: {', '.join(added)}")
