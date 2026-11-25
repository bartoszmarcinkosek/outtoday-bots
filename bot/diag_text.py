"""Tylko odczyt: pełny widoczny tekst stron z audit/fetch_urls.txt (requests, bez przeglądarki). Linie: TU|url|status  TX|tekst"""
import os, re, html, requests
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36", "Accept-Language": "en"}
for u in [l.strip() for l in open(os.path.join(os.path.dirname(__file__), "..", "audit", "fetch_urls.txt")) if l.strip().startswith("http")]:
    try:
        r = requests.get(u, headers=H, timeout=40); st, raw = r.status_code, r.text
    except Exception as e:
        st, raw = 0, str(e)[:100]
    print(f"TU|{u}|{st}|{len(raw)}")
    txt = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    out, prev = 0, None
    for l in html.unescape(re.sub(r"<[^>]+>", "\n", txt)).split("\n"):
        l = re.sub(r"\s+", " ", l).strip()
        if len(l) > 1 and l != prev:
            print("TX|" + l[:500]); out += len(l); prev = l
        if out > 14000:
            break
