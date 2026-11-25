"""Tylko odczyt: pobiera adresy z audit/fetch_urls.txt i wypisuje linki wewnętrzne oraz linie z cenami/godzinami/ofertami.
Linie: UU|url|status|długość   UL|link   UT|tekst"""
import os, re, html, requests
from urllib.parse import urljoin, urlparse
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36", "Accept-Language": "en"}
KEY = re.compile(r"AED|Dhs|\d{1,2}[:.]\d{2}|\d{1,2}\s*(am|pm)\b|day ?(use|pass)|brunch|buffet|offer|package|valid|until|friday|saturday|sunday|weekday|weekend|festive|new year|christmas|national day", re.I)
for u in [l.strip() for l in open(os.path.join(os.path.dirname(__file__), "..", "audit", "fetch_urls.txt")) if l.strip().startswith("http")]:
    try:
        r = requests.get(u, headers=H, timeout=30); st, raw = r.status_code, r.text
    except Exception as e:
        st, raw = 0, str(e)[:100]
    print(f"UU|{u}|{st}|{len(raw)}")
    links = sorted({urljoin(u, h).split("#")[0] for h in re.findall(r'href=["\']([^"\']+)', raw)})
    for l in links:
        if urlparse(l).netloc == urlparse(u).netloc and not re.search(r"\.(css|js|png|jpe?g|svg|ico|woff2?|xml)(\?|$)|wp-json|/feed|/tag/|/category/", l):
            print("UL|" + l[:160])
    txt = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", raw)
    seen, n = set(), 0
    for l in html.unescape(re.sub(r"<[^>]+>", "\n", txt)).split("\n"):
        l = re.sub(r"\s+", " ", l).strip()
        if 3 < len(l) < 500 and KEY.search(l) and l not in seen:
            seen.add(l); n += len(l); print("UT|" + l[:400])
        if n > 6000:
            break
