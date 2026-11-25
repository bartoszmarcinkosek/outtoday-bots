"""REGUŁA (25.11.2026, decyzja właściciela): MARTWE ŹRÓDŁA – automatyczna naprawa adresu.
Dla każdego źródła, którego strona zniknęła (404/410) albo przeniosła się na stałe (inny adres końcowy w tej samej domenie):
 1) przeniesiona -> wpisuje nowy adres,
 2) zniknęła -> szuka na stronie głównej tej samej domeny linku do wydarzeń (events / what's on / calendar / programme)
    i wpisuje go, jeśli ta strona odpowiada 200 i ma treść.
Niczego nie zgaduje: bez pewnego trafienia zostawia źródło bez zmian i wypisuje je do decyzji (linie RX|).
Nie rusza stron blokujących roboty (403, robots.txt) – te zastępujemy kontem Instagram (osobna reguła).
Bez AI. Linie: RF| naprawione, RX| do decyzji, RZ| podsumowanie. Próba: diag.yml ze skryptem source_repair. Zapis: workflow source-repair.yml (co tydzień)."""
import os, sys, re, json, glob, datetime as dt
from urllib.parse import urlparse, urljoin
sys.path.insert(0, os.path.dirname(__file__))
import requests
from bs4 import BeautifulSoup
import run as R

DRY = os.environ.get("REPAIR_WRITE") != "1"   # diag.yml = próba; source-repair.yml zapisuje
WORDS = re.compile(r"what.?s.?on|events?\b|calendar|programme|program\b|agenda|happenings", re.I)
BAD = re.compile(r"privacy|terms|career|login|account|cart|press|news|blog|corporate|venue-hire|book-an-event|private-events|meetings", re.I)


def get(url):
    try:
        r = requests.get(url, headers={"User-Agent": R.USER_AGENT}, timeout=25, allow_redirects=True)
        return r.status_code, r.url, r.text
    except Exception as e:
        return -1, url, type(e).__name__


def site(u):
    return urlparse(u).netloc.lower().removeprefix("www.")


def sane(old: str, new: str) -> bool:
    """Nowy adres nie może być blogiem/aktualnością, stroną z minionym rokiem, adresem innego źródła ani tym samym adresem inną wielkością liter."""
    if new.lower().rstrip("/") == old.lower().rstrip("/") or new.rstrip("/") in ALL:
        return False
    if BAD.search(urlparse(new).path):
        return False
    return not any(int(y) < dt.date.today().year for y in re.findall(r"20\d\d", urlparse(new).path))


ALL = set()
for f in glob.glob(os.path.join(os.path.dirname(__file__), "..", "sources", "*.json")):
    try:
        ALL |= {u.rstrip("/") for x in json.load(open(f)).get("sources", []) for u in x.get("urls") or []}
    except Exception:
        pass
fixed, ask, n = [], [], 0
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "sources", "*.json"))):
    d = json.load(open(f))
    if not (isinstance(d, dict) and isinstance(d.get("sources"), list)):
        continue
    changed = False
    for s in d["sources"]:
        for i, url in enumerate(s.get("urls") or []):
            n += 1
            ok, _ = R.robots_allows(url)
            if not ok:
                continue
            code, final, body = get(url)
            if code in (200, 403, 401, 429, -1) or code >= 500:
                # 200: działa (przeniesienie w tej samej domenie zapisujemy, gdy ścieżka naprawdę inna)
                if code == 200 and site(final) == site(url) and urlparse(final).path.rstrip("/") != urlparse(url).path.rstrip("/") \
                        and urlparse(final).path.strip("/") and WORDS.search(final) and sane(url, final):
                    s["urls"][i] = final; changed = True
                    fixed.append((s["id"], url, final, "przeniesiona"))
                continue
            if code not in (404, 410):
                continue
            home = f"{urlparse(url).scheme}://{urlparse(url).netloc}/"
            hc, hfinal, hbody = get(home)
            best = None
            if hc == 200:
                cands = []
                for a in BeautifulSoup(hbody, "html.parser").find_all("a", href=True):
                    href = urljoin(hfinal, a["href"]).split("#")[0]
                    label = a.get_text(" ", strip=True)[:80]
                    if site(href) != site(hfinal) or BAD.search(href) or href.rstrip("/") == hfinal.rstrip("/"):
                        continue
                    if WORDS.search(urlparse(href).path) or WORDS.fullmatch(label.strip()) or re.fullmatch(r"(what.?s on|events?|calendar)", label.strip(), re.I):
                        cands.append((len(urlparse(href).path), href))
                for _, href in sorted(set(cands))[:4]:
                    c2, f2, b2 = get(href)
                    if c2 == 200 and sane(url, f2) and len(BeautifulSoup(b2, "html.parser").get_text(" ", strip=True)) > 400:
                        best = f2; break
            if best:
                s["urls"][i] = best; changed = True
                s["note"] = ((s.get("note") or "") + f" Adres naprawiony automatycznie {dt.date.today().isoformat()} (stary: {url}).").strip()
                fixed.append((s["id"], url, best, "znaleziona na stronie głównej"))
            else:
                ask.append((s["id"], s.get("city"), s.get("name"), url, f"HTTP {code}, strona główna {hc}"))
    if changed and not DRY:
        json.dump(d, open(f, "w"), ensure_ascii=False, indent=1)
for x in fixed:
    print("RF|" + "|".join(x))
for x in ask:
    print("RX|" + "|".join(str(v) for v in x))
print(f"RZ|urls {n}|fixed {len(fixed)}|to decide {len(ask)}{' [próba]' if DRY else ''}")
