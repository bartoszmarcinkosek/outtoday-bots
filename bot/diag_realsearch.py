"""Kandydaci na prawdziwe zdjęcia miejsc z Wikimedia Commons (tylko wolne licencje) i Pexels (gdy jest sekret PEXELS_API_KEY). Czyta audit/real_search.txt: `<klucz> | <zapytanie>`.
Wypisuje RS|klucz|nr|tytuł|adres 1600px|szer x wys|licencja|autor i zapisuje arkusze /tmp/rs/<klucz>.jpg (artefakt real-search)."""
import io, os, re, time
THUMB = {}
import requests
from PIL import Image, ImageDraw
UA = {"User-Agent": "OutTodayBot/1.0 (https://outtoday.ae; finding freely licensed photos of UAE landmarks)"}
OK = re.compile(r"^(CC0|CC BY(-SA)? [234]\.0|CC BY(-SA)? 2\.5|Public domain|PD)", re.I)
os.makedirs("/tmp/rs", exist_ok=True)
src = os.path.join(os.path.dirname(__file__), "..", "audit", "real_search.txt")
for line in open(src, encoding="utf-8"):
    if "|" not in line or line.startswith("#"):
        continue
    key, q = [x.strip() for x in line.split("|", 1)]
    r = requests.get("https://commons.wikimedia.org/w/api.php", headers=UA, timeout=30, params={
        "action": "query", "generator": "search", "gsrnamespace": 6, "gsrsearch": q + " filetype:bitmap", "gsrlimit": 30,
        "prop": "imageinfo", "iiprop": "url|size|extmetadata", "iiurlwidth": 1600, "format": "json",
        "iiextmetadatafilter": "LicenseShortName|Artist"}).json()
    pages = sorted((r.get("query") or {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    cands = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = (md.get("LicenseShortName") or {}).get("value", "")
        art = re.sub("<[^>]+>", "", (md.get("Artist") or {}).get("value", "")).strip()[:60]
        if not OK.search(lic) or ii.get("width", 0) < 1000:
            continue
        cands.append((p["title"], ii.get("thumburl") or ii.get("url"), f"{ii.get('width')}x{ii.get('height')}", lic, art))
        if len(cands) >= 6:
            break
    # Pexels (licencja Pexels: darmowe użycie, także komercyjne, bez obowiązku podpisu; podpisujemy autora z grzeczności) – decyzja właściciela 27.11.2026
    pk = os.environ.get("PEXELS_API_KEY", "").strip()
    if pk:
        try:
            pr = requests.get("https://api.pexels.com/v1/search", headers={"Authorization": pk}, timeout=30,
                              params={"query": q, "per_page": 12, "orientation": "portrait"}).json()
            for ph in pr.get("photos", [])[:12 - min(len(cands), 6)]:
                alt = (ph.get("alt") or "").replace("|", "/")[:80]
                cands.append((f"Pexels: {alt}", ph["src"]["large2x"], f"{ph['width']}x{ph['height']}", "Pexels License",
                              f"{ph.get('photographer', '')} ({ph.get('url', '')})"))
        except Exception as e:  # noqa: BLE001
            print(f"RS|{key}|pexels error {e}")
    # Openverse (bez klucza): zdjęcia na wolnych licencjach z Flickra i innych serwisów – zamiast Pexels (Pexels wstrzymał nowe klucze API, 27.11.2026)
    try:
        ov = requests.get("https://api.openverse.org/v1/images/", headers=UA, timeout=30, params={
            "q": q, "license_type": "commercial", "page_size": 20, "mature": "false"}).json()
        n = 0
        for it in ov.get("results", []):
            lic = (it.get("license") or "").lower()
            # Flickr blokuje pobieranie przez boty (403) – nie obchodzimy tego, bierzemy tylko źródła, które pozwalają pobrać
            if lic not in ("by", "by-sa", "cc0", "pdm") or (it.get("width") or 0) < 1000 or "flickr" in (it.get("url") or ""):
                continue
            name = {"by": "CC BY", "by-sa": "CC BY-SA", "cc0": "CC0", "pdm": "Public domain"}[lic] + (f" {it.get('license_version')}" if lic in ("by", "by-sa") else "")
            THUMB[it["url"]] = it.get("thumbnail")
            cands.append((f"Openverse/{it.get('source', '')}: {(it.get('title') or '')[:70]}".replace("|", "/"), it["url"],
                          f"{it.get('width')}x{it.get('height')}", name, f"{(it.get('creator') or '')[:40]} ({it.get('foreign_landing_url', '')})"))
            n += 1
            if n >= 6:
                break
    except Exception as e:  # noqa: BLE001
        print(f"RS|{key}|openverse error {e}")
    cands = cands[:6] + [c for c in cands[6:] ] if len(cands) > 12 else cands
    cands = cands[:18]
    sheet = Image.new("RGB", (6 * 260, 3 * 300), "white"); d = ImageDraw.Draw(sheet)
    for i, (t, u, sz, lic, art) in enumerate(cands):
        print(f"RS|{key}|{i}|{t}|{u}|{sz}|{lic}|{art}")
        try:
            im = None
            for tu in [THUMB.get(u), u]:
                if not tu:
                    continue
                for _ in range(3):
                    rr = requests.get(tu, headers=UA, timeout=30)
                    if rr.ok and rr.headers.get("content-type", "").startswith("image"):
                        im = Image.open(io.BytesIO(rr.content)).convert("RGB"); break
                    time.sleep(3)
                if im:
                    break
            if im is None:
                raise RuntimeError("no image")
            im.thumbnail((256, 280))
            sheet.paste(im, ((i % 6) * 260, (i // 6) * 300)); d.text(((i % 6) * 260 + 2, (i // 6) * 300 + 282), str(i), fill="red")
        except Exception as e:  # noqa: BLE001
            print(f"RS|{key}|{i}|thumb error {e}")
    sheet.save(f"/tmp/rs/{key}.jpg", quality=80)
    print(f"RS|{key}|found {len(cands)}")
