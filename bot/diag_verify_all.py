"""Tylko odczyt: pełna kontrola całej bazy (decyzja właściciela 27.11.2026 „Zrób wszystko. Całą bazę danych”).
Dla każdego zatwierdzonego wydarzenia, oferty i miejsca z linkiem pobiera stronę (z poszanowaniem robots.txt) i sprawdza:
  - czy link działa (kod, adres końcowy, czy nie prowadzi do agregatora),
  - czy nazwa jest na stronie,
  - dla wydarzeń: czy data startu (albo dzień z zakresu) jest na stronie.
Najpierw zwykłe pobranie (szybkie), przeglądarka tylko gdy strona jest pusta albo nic nie pasuje.
Wynik: VA|kind|id|verdict|http|date_ok|name_hit|final_url|start|title  (verdict: OK / CHECK / DEAD / ROBOTS / AGGR / NOURL)
SHARD=i/n dzieli pracę między równoległe przebiegi."""
import os, re, sys, json, datetime as dt
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
from urllib.parse import urlparse
import requests
sys.path.insert(0, os.path.dirname(__file__))
import run as R

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
si, sn = (int(x) for x in os.environ.get("SHARD", "0/1").split("/"))
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date()

items = []
for r in db.get("events", {"select": "id,title,start_date,end_date,venue,official_url", "status": "eq.approved",
                           "or": f"(end_date.gte.{today},and(end_date.is.null,start_date.gte.{today}))", "limit": "10000"}):
    items.append(("event", r["id"], r.get("title") or "", r.get("official_url"), r.get("start_date"), r.get("end_date")))
for r in db.get("deals", {"select": "id,title,venue,official_url", "status": "eq.approved", "limit": "10000"}):
    items.append(("deal", r["id"], (r.get("venue") or r.get("title") or ""), r.get("official_url"), None, None))
for r in db.get("places", {"select": "id,name,official_url", "status": "eq.approved", "limit": "10000"}):
    items.append(("place", r["id"], r.get("name") or "", r.get("official_url"), None, None))

urls = sorted({(it[3] or "").strip() for it in items if (it[3] or "").strip()})
mine = {u for i, u in enumerate(urls) if i % sn == si}
print(f"VA|INFO|items {len(items)} | urls {len(urls)} | shard {si}/{sn}: {len(mine)}")

MON = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
FULL = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]


def date_pats(d: dt.date) -> list[str]:
    m, mf, day = MON[d.month - 1], FULL[d.month - 1], d.day
    sfx = r"(st|nd|rd|th)?"
    return [rf"\b0?{day}{sfx}\s*(of\s*)?({mf}|{m})\b", rf"\b({mf}|{m})\.?\s*0?{day}{sfx}\b", rf"\b0?{day}[/.\-]0?{d.month}[/.\-](20)?\d\d\b",
            rf"\b{d.isoformat()}\b", rf"\b0?{day}\s*[-–]\s*\d{{1,2}}\s*({mf}|{m})\b", rf"\b\d{{1,2}}\s*[-–]\s*0?{day}\s*({mf}|{m})\b"]


def date_ok(text: str, s, e) -> bool:
    if not s:
        return True
    t = text.lower()
    d0 = dt.date.fromisoformat(s)
    d1 = dt.date.fromisoformat(e) if e else d0
    if (d1 - d0).days > 45:  # długie sezony / stałe atrakcje: wystarczy miesiąc startu albo końca
        return any(re.search(rf"\b({FULL[d.month-1]}|{MON[d.month-1]})\b", t) for d in (d0, d1))
    d = d0
    while d <= d1:
        if any(re.search(p, t) for p in date_pats(d)):
            return True
        d += dt.timedelta(days=1)
    return False


STOP = {"dubai", "abu", "dhabi", "sharjah", "ajman", "fujairah", "the", "and", "with", "live", "night", "day", "presents", "featuring",
        "show", "concert", "tour", "edition", "event", "festival", "brunch", "ladies", "happy", "hour", "park", "beach", "museum", "centre", "center", "hotel", "resort", "club", "bar"}


def name_hit(text: str, name: str) -> float:
    toks = [w for w in re.findall(r"[a-z0-9]{3,}", R.norm(name)) if w not in STOP]
    if not toks:
        return 1.0
    t = R.norm(text)
    return sum(1 for w in toks if w in t) / len(toks)


def get_plain(url: str):
    try:
        r = requests.get(url, headers={"User-Agent": R.USER_AGENT, "Accept-Language": "en"}, timeout=25, allow_redirects=True)
        txt = re.sub(r"<script.*?</script>|<style.*?</style>", " ", r.text, flags=re.S | re.I)
        txt = re.sub(r"<[^>]+>", " ", txt)
        return r.status_code, r.url, re.sub(r"\s+", " ", txt)
    except Exception as ex:  # noqa: BLE001
        return -1, url, str(ex)[:80]


plain = {}
bydom = defaultdict(list)
for u in mine:
    bydom[urlparse(u).netloc].append(u)


def do_domain(dom):
    out = {}
    for u in bydom[dom]:
        ok, why = R.robots_allows(u)
        out[u] = ("ROBOTS", 0, u, "") if not ok else get_plain(u)
    return out


with ThreadPoolExecutor(8) as ex:
    for res in ex.map(do_domain, list(bydom)):
        plain.update(res)

need_browser = set()
for it in items:
    u = (it[3] or "").strip()
    if u not in plain or plain[u][0] == "ROBOTS":
        continue
    code, fin, txt = plain[u]
    if code == -1 or code >= 400 or len(txt) < 800 or name_hit(txt, it[2]) < 0.5 or (it[0] == "event" and not date_ok(txt, it[4], it[5])):
        need_browser.add(u)

pages = {u: (v[0], v[1], v[2]) for u, v in plain.items()}
if need_browser:
    with R.Browser() as br:
        for u in sorted(need_browser):
            try:
                p = br.fetch(u)
                pages[u] = (p.get("status") or 200, p.get("final_url") or u, (p.get("full_text") or p.get("text") or "") + " " + pages[u][2])
            except Exception as e:  # noqa: BLE001
                pass

for it in items:
    kind, iid, name, url, s, e = it
    url = (url or "").strip()
    if not url:
        if si == 0:
            print(f"VA|{kind}|{iid}|NOURL|||||{s or ''}|{name[:70]}")
        continue
    if url not in pages:
        continue
    code, fin, txt = pages[url]
    if code == "ROBOTS":
        v, dok, nh = "ROBOTS", "", ""
    else:
        host = urlparse(fin).netloc.lower()
        dok = date_ok(txt, s, e) if kind == "event" else True
        nh = round(name_hit(txt, name), 2)
        if code == -1 or (isinstance(code, int) and code >= 400):
            v = "DEAD"
        elif host.startswith("queue.") or "protectallsite" in fin:
            v = "BLOCKED"  # kolejka antybotowa sprzedawcy – nie da się sprawdzić automatycznie
        elif any(a in host for a in ("instagram.com", "facebook.com", "tiktok.com", "x.com", "twitter.com")):
            v = "SOCIAL"
        elif urlparse(fin).path.strip("/").lower() in ("", "en", "en/abu-dhabi", "en/dubai", "abu-dhabi", "dubai", "en/events", "events", "event/list"):
            v = "GENERIC"  # link do strony głównej / listy, nie do tego wydarzenia
        elif any(a in host for a in R.AGGREGATORS) and not any(t in host for t in ("platinumlist", "feverup")):
            v = "AGGR"
        elif nh >= 0.5 and dok:
            v = "OK"
        else:
            v = "CHECK"
    print("VA|" + "|".join(str(x).replace("|", "/")[:90] for x in (kind, iid, v, code, dok, nh, fin, s or "", name[:70])))
