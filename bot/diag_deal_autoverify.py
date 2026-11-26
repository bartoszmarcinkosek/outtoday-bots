"""Tylko odczyt, bez AI: szybkie porównanie WSZYSTKICH niesprawdzonych ofert z ich stroną (prośba właściciela 26.11.2026:
„może jeszcze szybciej”). Każdy adres otwierany raz prawdziwą przeglądarką (jak boty, szanuje robots.txt).
Oferta jest zgodna (AV), gdy strona działa, wymienia ofertę (charakterystyczne słowo z tytułu/miejsca)
i podaje te same kwoty AED co u nas (albo, przy ofercie bez ceny, tę samą godzinę startu).
Linie: AV|id (zgodna) · AX|id|powód|cena u nas|fragment strony (różnica) · AN|id|nie ma oferty na stronie · AD|id|martwy link|status
· AU|id|nieczytelna|powód · AZ| podsumowanie. Pominięte: sprawdzone w ostatnich 14 dniach (audit/deal_verified.json)."""
import datetime as dt, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ROOT = os.path.join(os.path.dirname(__file__), "..")
try:
    ver = json.load(open(os.path.join(ROOT, "audit", "deal_verified.json")))
except Exception:
    ver = {}
fresh = (R.today_uae() - dt.timedelta(days=14)).isoformat()
deals = [d for d in db.get("deals", {"select": "id,title,venue,price_text,start_time,official_url,days_of_week", "status": "eq.approved", "limit": "3000"})
         if ver.get(d["id"], "") < fresh]
GENERIC = set("""lunch brunch breakfast dinner happy hour hours ladies lady night nights quiz day pass staycation out daily weekday weekdays weekend
weekly business offer offers deal deals special specials menu set buffet the and with at a an our of all evening morning friday saturday sunday
weekends adult adults kids only hotel resort in on for per person monday tuesday wednesday thursday every pool beach access package promo promotion
bar restaurant lounge club dubai abu dhabi sharjah ajman fujairah ras al khaimah umm quwain ain by de la le night's ladies' unlimited free drinks
house beverages beverage soft package packages from aed vat""".split())


def words(*s):
    return {w for w in re.findall(r"[a-z][a-z'’]{3,}", " ".join(x or "" for x in s).lower()) if w not in GENERIC}


def nums(t):
    return {n.replace(",", "") for n in re.findall(r"(?<![\d.])(\d{2,5}(?:,\d{3})?)(?![\d])", t or "") if 10 <= int(n.replace(",", "")) <= 20000}


def hour_forms(hm):
    h, m = int(hm[:2]), int(hm[3:5])
    h12 = h % 12 or 12
    ap = "pm" if h >= 12 else "am"
    f = {f"{h:02d}:{m:02d}", f"{h}:{m:02d}", f"{h12}:{m:02d}{ap}", f"{h12}:{m:02d} {ap}", f"{h12}.{m:02d}{ap}", f"{h12}.{m:02d} {ap}"}
    if m == 0:
        f |= {f"{h12}{ap}", f"{h12} {ap}", f"{h12}{ap[0]}"}
    return f


by_url = {}
for d in deals:
    by_url.setdefault((d.get("official_url") or "").strip(), []).append(d)
cnt = {}


def out(code, line):
    cnt[code] = cnt.get(code, 0) + 1
    print(line)


for d in by_url.get("", []):
    out("AU", f"AU|{d['id']}|brak linku")
with R.Browser() as br:
    for u, ds in by_url.items():
        if not u:
            continue
        ok, why = R.robots_allows(u)
        if not ok:
            for d in ds:
                out("AU", f"AU|{d['id']}|{why}")
            continue
        try:
            p = br.fetch(u)
        except Exception as e:
            for d in ds:
                out("AU", f"AU|{d['id']}|błąd {type(e).__name__}")
            continue
        st = p.get("status") or 0
        txt = re.sub(r"\s+", " ", p.get("full_text") or p.get("text") or "")
        low = txt.lower()
        if st in (404, 410):
            for d in ds:
                out("AD", f"AD|{d['id']}|martwy link|{st}")
            continue
        if st >= 400 or len(txt) < 300:
            for d in ds:
                out("AU", f"AU|{d['id']}|status {st}, tekst {len(txt)} znaków")
            continue
        page_nums = nums(txt)
        for d in ds:
            w = words(d["title"], d.get("venue"))
            hit = [x for x in w if x in low]
            if w and not hit:
                out("AN", f"AN|{d['id']}|nie ma oferty na stronie|{d['title']}|{u}")
                continue
            ours = nums(d.get("price_text"))
            if ours:
                miss = ours - page_nums
                if miss:
                    i = low.find("aed")
                    out("AX", f"AX|{d['id']}|kwoty {','.join(sorted(miss))} nie ma na stronie|{d.get('price_text')}|{txt[max(0, i - 80):i + 160] if i >= 0 else ''}")
                    continue
                out("AV", f"AV|{d['id']}")
            elif d.get("start_time") and any(f in low for f in hour_forms(str(d["start_time"]))):
                out("AV", f"AV|{d['id']}")
            else:
                out("AX", f"AX|{d['id']}|bez ceny, a godziny {d.get('start_time')} nie ma na stronie|{d.get('price_text')}|")
print(f"AZ|ofert do sprawdzenia {len(deals)} | adresów {len(by_url)} | " + " ".join(f"{k}={v}" for k, v in sorted(cnt.items())))
