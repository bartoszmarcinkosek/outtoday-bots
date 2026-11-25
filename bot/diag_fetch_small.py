"""Tylko odczyt: pobiera strony źródłowe ofert i wydarzeń z małych emiratów i wypisuje fragmenty z cenami/godzinami
(do ręcznego porównania). Linie: FU|url|status|długość   FT|fragment"""
import os, sys, re, datetime as dt, html
sys.path.insert(0, os.path.dirname(__file__))
import run as R, requests
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
C = ("Ras Al Khaimah", "Ajman", "Umm Al Quwain", "Fujairah", "Al Ain")
SKIP = set(os.environ.get("SKIP", "").split())
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date().isoformat()
urls = {}
for r in db.get("deals", {"select": "id,title,venue,city,official_url,price_text", "status": "eq.approved", "limit": "3000"}):
    u = r.get("official_url") or ""
    if r.get("city") in C and u.startswith("http") and "instagram" not in u:
        urls.setdefault(u, []).append(r["title"])
for r in db.get("events", {"select": "id,title,city,start_date,end_date,official_url", "status": "eq.approved", "limit": "5000"}):
    u = r.get("official_url") or ""
    if r.get("city") in C and u.startswith("http") and "instagram" not in u and today <= (r.get("end_date") or r["start_date"]) and r["start_date"] <= "2026-12-20":
        urls.setdefault(u, []).append(r["title"])
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36", "Accept-Language": "en"}
KEY = re.compile(r"AED|Dhs|\bDH\b|\d{1,2}[:.]\d{2}\s*(am|pm)?|\d{1,2}\s*(am|pm)\b|monday|tuesday|wednesday|thursday|friday|saturday|sunday|sold out|cancel|postpon|valid|until", re.I)
for u, titles in sorted(urls.items()):
    if any(s in u for s in SKIP):
        continue
    try:
        r = requests.get(u, headers=H, timeout=25)
        st, txt = r.status_code, r.text
    except Exception as e:
        st, txt = 0, str(e)[:80]
    txt = re.sub(r"(?is)<(script|style|noscript|svg)[^>]*>.*?</\1>", " ", txt)
    txt = html.unescape(re.sub(r"<[^>]+>", "\n", txt))
    lines = [re.sub(r"\s+", " ", l).strip() for l in txt.split("\n")]
    lines = [l for l in lines if 3 < len(l) < 400]
    print(f"FU|{u}|{st}|{len(txt)}|{' ; '.join(t[:40] for t in titles)}")
    words = {w for t in titles for w in re.findall(r"[a-z]{4,}", t.lower())} - {"night", "pass", "brunch", "with", "from", "hour", "happy", "beach", "resort", "hotel"}
    out, n = [], 0
    for i, l in enumerate(lines):
        if KEY.search(l) or any(w in l.lower() for w in words):
            if l not in out:
                out.append(l); n += len(l)
        if n > 1800:
            break
    for l in out:
        print("FT|" + l[:300])
