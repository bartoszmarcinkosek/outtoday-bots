"""Buduje app/src/photos_remote.gen.ts z photos/unsplash.txt.
Dla nowych zdjęć: pobiera dane zdjęcia z API (adres, autor, proporcje) i zgłasza pobranie (download_location) –
oba wymagane przez zasady Unsplash API. Dane trzymamy w photos/unsplash_cache.json, żeby nie zużywać limitu (50/h)."""
import json, os, sys, requests
ROOT = os.path.join(os.path.dirname(__file__), "..")
KEY = os.environ.get("UNSPLASH_KEY", "").strip()
H = {"Authorization": f"Client-ID {KEY}", "Accept-Version": "v1"}
cache_p = os.path.join(ROOT, "photos", "unsplash_cache.json")
cache = json.load(open(cache_p))
rows = []
for line in open(os.path.join(ROOT, "photos", "unsplash.txt"), encoding="utf-8"):
    if line.startswith("#") or "|" not in line:
        continue
    parts = [x.strip() for x in line.split("|")]
    rows.append((parts[0], parts[1], (parts[2] if len(parts) > 2 and parts[2] else "entropy")))
budget = 46  # limit demo 50/h; reszta przy następnym uruchomieniu
for name, pid, _ in rows:
    if pid in cache:
        continue
    if not KEY or budget < 2:
        print(f"UP|{name}|{pid}|later (limit)"); continue
    r = requests.get(f"https://api.unsplash.com/photos/{pid}", headers=H, timeout=30); budget -= 1
    rem = r.headers.get("X-Ratelimit-Remaining")
    if rem is not None and rem.isdigit(): budget = min(budget, int(rem))
    if r.status_code == 403 and "Rate Limit" in r.text:
        print(f"UP|{name}|{pid}|later (limit)"); budget = 0; continue
    if not r.ok:
        print(f"UP|{name}|{pid}|ERROR {r.status_code}"); continue
    j = r.json()
    d = requests.get(j["links"]["download_location"], headers=H, timeout=30); budget -= 1
    cache[pid] = {"raw": j["urls"]["raw"], "w": j["width"], "h": j["height"], "author": j["user"]["name"],
                  "authorUrl": j["user"]["links"]["html"], "link": j["links"]["html"], "dl": d.status_code}
    print(f"UP|{name}|{pid}|added {j['user']['name']} {j['width']}x{j['height']} download={d.status_code}")
json.dump(cache, open(cache_p, "w"), indent=1, ensure_ascii=False)
out = ["// Plik generowany przez bot/unsplash_photos.py z photos/unsplash.txt – nie edytuj ręcznie.",
       "// Zdjęcia ładowane z Unsplash (hotlink, zgodnie z zasadami Unsplash API).",
       "export type RemotePhoto = { name: string; raw: string; ratio: number; author: string; authorUrl: string; link: string; crop: string };",
       "export const REMOTE_PHOTOS: RemotePhoto[] = ["]
n = 0
for name, pid, crop in rows:
    c = cache.get(pid)
    if not c:
        continue
    out.append("  " + json.dumps({"name": name, "raw": c["raw"], "ratio": round(c["w"] / c["h"], 3), "author": c["author"],
                                  "authorUrl": c["authorUrl"], "link": c["link"], "crop": crop}, ensure_ascii=False) + ",")
    n += 1
out.append("];")
open(os.path.join(ROOT, "app", "src", "photos_remote.gen.ts"), "w", encoding="utf-8").write("\n".join(out) + "\n")
print(f"UP|SUMMARY|{n} photos")
