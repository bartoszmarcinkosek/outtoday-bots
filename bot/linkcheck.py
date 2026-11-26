"""OutToday: darmowa kontrola, dokąd prowadzą linki (bez AI). Tylko odczyt.
Dla każdej zatwierdzonej pozycji pobiera official_url i sprawdza: błąd HTTP, przekierowanie na stronę główną,
brak słów z tytułu/miejsca w treści strony. Linie: LK|kod|tabela|id|miasto|tytuł|url|szczegół."""
from __future__ import annotations
import collections, concurrent.futures as cf, os, re, sys
from urllib.parse import urlparse
import requests
sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
T = R.today_uae().isoformat()
SKIP = ("instagram.com", "facebook.com", "tiktok.com", "wa.me", "whatsapp", "linkedin.com", "x.com", "twitter.com")
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
      "Accept-Language": "en-US,en;q=0.9"}
STOP = set("the a an at in of and with for to by on from live show night day special edition dubai abu dhabi sharjah ajman uae al ras khaimah "
           "fujairah hotel resort restaurant bar lounge club beach offer deal brunch happy hour ladies breakfast lunch dinner pass pool 2026 2027".split())
items = []
for r in db.get("events", {"select": "id,title,venue,city,official_url", "status": "eq.approved", "or": f"(end_date.gte.{T},start_date.gte.{T})", "limit": "5000"}):
    items.append(("events", r, r["title"], r.get("venue") or ""))
for r in db.get("deals", {"select": "id,title,venue,city,official_url", "status": "eq.approved", "limit": "5000"}):
    items.append(("deals", r, r.get("title") or "", r.get("venue") or ""))
for r in db.get("places", {"select": "id,name,city,official_url", "status": "eq.approved", "limit": "5000"}):
    items.append(("places", r, r["name"], ""))
items = [i for i in items if (i[1].get("official_url") or "").startswith("http")]
urls = sorted({i[1]["official_url"] for i in items if not any(s in urlparse(i[1]["official_url"]).netloc for s in SKIP)})
print(f"LA|items with link {len(items)} | unique urls to fetch {len(urls)}")


def fetch(u):
    try:
        r = requests.get(u, headers=UA, timeout=25, allow_redirects=True)
        return u, r.status_code, r.url, re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", r.text[:600000], flags=re.S | re.I)
    except requests.RequestException as e:
        # 26.11.2026: domena, która nie istnieje (DNS NXDOMAIN), to martwy link, nie blokada robotów
        if re.search(r"NameResolution|getaddrinfo|Name or service not known|nodename nor servname|No address associated", str(e)):
            return u, -404, u, "domain does not exist"
        return u, 0, u, type(e).__name__


with cf.ThreadPoolExecutor(8) as ex:
    pages = {u: (st, fin, txt) for u, st, fin, txt in ex.map(fetch, urls)}
words = lambda s: [w for w in re.findall(r"[a-z0-9]{3,}", R.norm(s)) if w not in STOP]
cnt = collections.Counter()
for table, r, title, venue in items:
    u = r["official_url"]
    if u not in pages:
        continue
    st, fin, txt = pages[u]
    code = detail = ""
    p0, p1 = urlparse(u), urlparse(fin)
    if st == -404:
        code, detail = "NOT_FOUND", "domain does not exist"
    elif st == 0:
        code, detail = "NO_RESPONSE", txt
    elif st in (404, 410):
        code, detail = "NOT_FOUND", st
    elif st >= 400:
        code, detail = "BLOCKED_OR_ERROR", st      # często blokada robotów – tylko informacyjnie
    elif p1.netloc.startswith("queue."):
        code, detail = "BLOCKED_OR_ERROR", "waiting room"   # kolejka biletowni (Platinumlist) – strona istnieje
    elif len(p0.path.strip("/")) > 3 and len(p1.path.strip("/")) <= 3 and p0.netloc.split(".")[-2:] == p1.netloc.split(".")[-2:]:
        code, detail = "REDIRECT_HOME", fin
    else:
        body = R.norm(re.sub(r"<[^>]+>", " ", txt))
        tw, vw = words(title), words(venue.split(",")[0])
        th = sum(w in body for w in tw)
        vh = sum(w in body for w in vw)
        if len(body) < 400:
            code, detail = "EMPTY_PAGE", len(body)  # strona ładowana skryptem – nie da się ocenić
        elif tw and th == 0 and (not vw or vh == 0):
            code, detail = "NO_MATCH", f"title words {tw[:5]} venue words {vw[:4]} not on page"
        elif table == "events" and len(tw) >= 2 and th / len(tw) < 0.34 and len(p1.path.strip("/")) <= 3:
            code, detail = "HOME_NOT_EVENT", f"{th}/{len(tw)} title words; link is a home page"
    if code:
        cnt[code] += 1
        print("LK|" + "|".join(str(x).replace("|", "/")[:160] for x in (code, table, r["id"], r.get("city") or "", title[:70], u, detail)))
print("LA|" + " ".join(f"{k}={v}" for k, v in sorted(cnt.items())))
