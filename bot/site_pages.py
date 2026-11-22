"""Strony udostępnianych wpisów na outtodayapp.github.io (uruchamiane z repo strony, co kilka godzin, koszt 0 USD).
Dla każdego zatwierdzonego, aktualnego eventu / miejsca / oferty tworzy e/<rodzaj>-<id>.html z tagami Open Graph,
dzięki którym WhatsApp, Instagram itd. pokazują w wiadomości tytuł, opis i ZDJĘCIE (to samo co w apce).
Dane: publiczny klucz bazy (tylko zatwierdzone wpisy). Zdjęcia: app/assets/photos/full. Reguły doboru zdjęć czytane z app/src/photos.ts.
Użycie: python bot/site_pages.py <katalog_strony>"""
import datetime as dt
import html
import json
import os
import re
import shutil
import sys

import requests

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT = sys.argv[1]
SITE = "https://outtodayapp.github.io"
URL = "https://ibpuispeimyyqiailjfy.supabase.co"
KEY = "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"  # publiczny klucz apki (tylko odczyt zatwierdzonych wpisów)
H = {"apikey": KEY, "Authorization": f"Bearer {KEY}"}
# Linki do sklepów: wpisz, gdy apka będzie publicznie dostępna (wtedy na stronach pojawi się przycisk "Get the app").
PLAY_URL = ""      # np. https://play.google.com/store/apps/details?id=ae.outtoday.app
APPSTORE_URL = ""  # np. https://apps.apple.com/app/id...
GETAPP = (" ".join(f'<a href="{u}">{n}</a>' for n, u in (("Google Play", PLAY_URL), ("App Store", APPSTORE_URL)) if u)
          or '<span class="soon">Coming soon</span>')
today = dt.datetime.now(dt.timezone(dt.timedelta(hours=4))).date().isoformat()

# ---- reguły zdjęć z app/src/photos.ts (jedno źródło prawdy z apką)
ts = open(os.path.join(ROOT, "app/src/photos.ts"), encoding="utf-8").read()
lm_block = ts[ts.index("const LANDMARKS"):ts.index("const RULES")]
rules_block = ts[ts.index("const RULES"):ts.index("const CAT")]
cat_block = ts[ts.index("const CAT"):ts.index("const CITY_SUFFIX")]
pat = re.compile(r"\[/(.+?)/i, '(\w+)'\]")
LANDMARKS = [(re.compile(a.replace("\\/", "/"), re.I), b) for a, b in pat.findall(lm_block)]
RULES = [(re.compile(a.replace("\\/", "/"), re.I), b) for a, b in pat.findall(rules_block)]
CAT = {k: re.findall(r"'(\w+)'", v) for k, v in re.findall(r"(\w+): \[([^\]]*)\]", cat_block)}
NO_FALLBACK = set(re.findall(r"'(\w+)'", ts[ts.index("const NO_FALLBACK"):].split("\n")[0]))
CITY_SUFFIX = {"Dubai": "dubai", "Abu Dhabi": "abudhabi", "Sharjah": "sharjah", "Ras Al Khaimah": "rak"}

photo_dir = os.path.join(ROOT, "app/assets/photos")
files = sorted(f for f in os.listdir(photo_dir) if f.endswith(".jpg"))
FILES: dict[str, list[str]] = {}
for f in files:
    FILES.setdefault(re.sub(r"-\d+\.jpg$", "", f), []).append(f)


def fnv(s: str) -> int:  # to samo co hash() w photos.ts
    h = 2166136261
    for ch in s.encode("utf-16-le").decode("utf-16-le"):
        h = ((h ^ ord(ch)) * 16777619) & 0xFFFFFFFF
    return h


def photo_for(kind: str, key: str, title: str, place_text: str, cat: str, city: str, avoid: str | None = None) -> str | None:
    lm = next((k for r, k in LANDMARKS if r.search(place_text)), None)
    if lm and lm in FILES:
        pool = FILES[lm]
    else:
        keys = None
        if kind != "deal" or not cat or cat == "other":
            hit = next((k for r, k in RULES if r.search(title)), None)
            if hit and hit in FILES:
                keys = [hit]
            elif hit in NO_FALLBACK:
                return None
        if not keys and kind == "event":
            return None  # jak w apce: event bez rozpoznanego rodzaju = ikonka, nie zdjęcie kategorii
        keys = keys or CAT.get(cat, [])
        suf = CITY_SUFFIX.get(city)
        pool = []
        for k in keys:
            pool += FILES.get(k, [])
            if suf:
                pool += FILES.get(f"{k}_{suf}", [])
    if not pool:
        return None
    i = fnv(key) % len(pool)
    if len(pool) > 1 and pool[i] == avoid:  # jak w apce: inne niż poprzednia karta
        i = (i + 1) % len(pool)
    return pool[i]


def get(table: str, cols: str, extra: str = "") -> list:
    out, off = [], 0
    while True:
        r = requests.get(f"{URL}/rest/v1/{table}?status=eq.approved&select={cols}{extra}&limit=1000&offset={off}", headers=H, timeout=60)
        r.raise_for_status()
        rows = r.json()
        out += rows
        if len(rows) < 1000:
            return out
        off += 1000


ev = get("events", "id,title,category,start_date,end_date,start_time,end_time,venue,area,city,price_text,is_free,description,official_url,url",
         f"&or=(end_date.gte.{today},and(end_date.is.null,start_date.gte.{today}))")
pl = get("places", "id,name,category,area,city,hours_text,price_text,is_free,description,official_url")
dl = get("deals", "id,title,deal_type,venue,area,city,price_text,details,start_time,end_time,official_url")

LABEL = {"music": "Music & Shows", "culture": "Culture & Art", "sport": "Sport & Fitness", "food": "Food & Drinks", "festivals": "Festivals",
         "nightlife": "Nightlife", "classes": "Classes & Workshops", "nature": "Nature & Outdoors", "community": "Community", "family": "Family",
         "market": "Markets", "beaches": "Beaches & Pools", "parks": "Parks & Nature", "museums": "Museums & Culture", "attractions": "Attractions",
         "active": "Sport & Active", "kids": "Kids & Play", "markets": "Markets & Malls", "studios": "Classes & Studios", "daytrips": "Day Trips",
         "day_pass": "Day pass", "brunch": "Brunch", "ladies_night": "Ladies' night", "happy_hour": "Happy hour", "night_out": "Night out",
         "lunch": "Business lunch", "dinner": "Dinner deal", "quiz": "Quiz night", "breakfast": "Breakfast", "staycation": "Staycation"}


def fmt(d: str | None) -> str:
    return dt.date.fromisoformat(d).strftime("%a %d %b %Y").replace(" 0", " ") if d else ""


def hm(t: str | None) -> str:
    return (t or "")[:5]


e = lambda v: html.escape(str(v or ""), quote=True)  # noqa: E731
TPL = open(os.path.join(ROOT, "bot/site_page.html"), encoding="utf-8").read().replace("{{GETAPP}}", GETAPP)

os.makedirs(os.path.join(OUT, "e"), exist_ok=True)
os.makedirs(os.path.join(OUT, "img"), exist_ok=True)
used = set()
keep = set()
for kind, rows in (("event", ev), ("place", pl), ("deal", dl)):
    for x in rows:
        title = x.get("title") or x.get("name") or ""
        cat = x.get("category") or x.get("deal_type") or ""
        where = " · ".join(v for v in (x.get("venue"), x.get("area"), x.get("city")) if v)
        if kind == "event":
            when = fmt(x["start_date"]) + (f" – {fmt(x['end_date'])}" if x.get("end_date") and x["end_date"] != x["start_date"] else "")
            if x.get("start_time"):
                when += f" · {hm(x['start_time'])}" + (f"–{hm(x['end_time'])}" if x.get("end_time") else "")
        elif kind == "place":
            when = x.get("hours_text") or ""
        else:
            when = f"{hm(x.get('start_time'))}–{hm(x.get('end_time'))}" if x.get("start_time") else ""
        price = (x.get("price_text") or "Free") if x.get("is_free") else (x.get("price_text") or "")
        desc = x.get("description") or x.get("details") or ""
        key = f"{kind}:{x['id']}"
        img = photo_for(kind, key, title, f"{title} {where}", cat, x.get("city") or "")
        if img:
            used.add(img)
        summary = " · ".join(v for v in (when, where, price) if v)
        off = x.get("official_url") or x.get("url") or ""
        rows_html = "".join(f'<p class="row"><b>{k}</b> {e(v)}</p>' for k, v in (("When", when), ("Where", where), ("Price", price)) if v)
        page = (TPL.replace("{{TITLE}}", e(title)).replace("{{OG_DESC}}", e((summary + (" — " + desc if desc else ""))[:280]))
                .replace("{{OG_IMAGE}}", f"{SITE}/apple-touch-icon.png")
                .replace("{{URL}}", f"{SITE}/e/{kind}-{x['id']}.html").replace("{{LABEL}}", e(LABEL.get(cat, "OutToday")))
                .replace("{{IMG}}", f'<img class="photo" src="../img/{img}" alt="">' if img else "")
                .replace("{{ROWS}}", rows_html).replace("{{DESC}}", f'<p class="desc">{e(desc)}</p>' if desc else "")
                .replace("{{OFFICIAL}}", f'<a class="btn ghost" href="{e(off)}" target="_blank" rel="noopener">Official page &amp; tickets</a>' if off.startswith("http") else ""))
        name = f"{kind}-{x['id']}.html"
        keep.add(name)
        with open(os.path.join(OUT, "e", name), "w", encoding="utf-8") as fh:
            fh.write(page)

# ---- strona główna "What's on in the UAE today": najważniejsze eventy na dziś i na weekend w każdym mieście (bez całej bazy)
BIG = re.compile(r"etihad arena|etihad park|coca[- ]cola arena|louvre|dubai opera|expo city|global village|yas marina|yas island|yas bay|"
                 r"ferrari world|warner bros|qasr al watan|sheikh zayed festival|liwa|al dhafra|mother of the nation|zayed sports city|"
                 r"museum of the future|cultural foundation|manarat|sharjah light|al majaz|al qasba|meydan|grand prix|marathon|festival|national day|eid al etihad", re.I)
CITIES = ["Dubai", "Abu Dhabi", "Sharjah", "Al Ain", "Ras Al Khaimah", "Ajman", "Fujairah", "Umm Al Quwain"]
td = dt.date.fromisoformat(today)
fri = td + dt.timedelta(days=(4 - td.weekday()) % 7)  # piątek tego tygodnia (albo dziś)
wk = [fri + dt.timedelta(days=i) for i in range(3)]


def on(x: dict, day: dt.date) -> bool:
    return x["start_date"] <= day.isoformat() <= (x.get("end_date") or x["start_date"])


def rank(x: dict) -> tuple:
    big = bool(BIG.search(f"{x['title']} {x.get('venue') or ''}"))
    single = not x.get("end_date") or x["end_date"] == x["start_date"]
    return (not big, not single, x.get("start_time") or "99", x["title"])


def card(x: dict) -> str:
    key = f"event:{x['id']}"
    global prev_img
    img = photo_for("event", key, x["title"], f"{x['title']} {x.get('venue') or ''} {x.get('area') or ''}", x.get("category") or "", x.get("city") or "", prev_img)
    prev_img = img
    if img:
        used.add(img)
    when = fmt(x["start_date"]) if not x.get("end_date") or x["end_date"] == x["start_date"] else f"{fmt(x['start_date'])} – {fmt(x['end_date'])}"
    if x.get("start_time"):
        when += f" · {hm(x['start_time'])}"
    price = (x.get("price_text") or "Free") if x.get("is_free") else (x.get("price_text") or "")
    sub = " · ".join(v for v in (x.get("venue"), price) if v)
    pic = f'<img src="img/{img}" alt="" loading="lazy">' if img else '<span class="noimg"></span>'
    return (f'<a class="ev" href="e/event-{x["id"]}.html">{pic}<span><b>{e(x["title"])}</b>'
            f'<small>{e(when)}</small><small>{e(sub)}</small></span></a>')


tabs, panels = [], []
prev_img = None
for i, city in enumerate(CITIES):
    mine = [x for x in ev if (x.get("city") or "") == city]
    t_list = sorted((x for x in mine if on(x, td)), key=rank)[:10]
    t_ids = {x["id"] for x in t_list}
    w_list = sorted((x for x in mine if x["id"] not in t_ids and any(on(x, d) for d in wk if d > td)), key=rank)[:10]
    if not t_list and not w_list:
        continue
    slug = city.lower().replace(" ", "-")
    tabs.append(f'<button data-c="{slug}"{" class=on" if not tabs else ""}>{e(city)}</button>')
    body = ""
    if t_list:
        body += f"<h3>Today in {e(city)}</h3>" + "".join(card(x) for x in t_list)
    if w_list:
        body += f"<h3>This weekend in {e(city)}</h3>" + "".join(card(x) for x in w_list)
    panels.append(f'<section id="{slug}"{"" if len(panels) == 0 else " hidden"}><h2>What\'s on in {e(city)}</h2>{body}</section>')
home = (open(os.path.join(ROOT, "bot/site_home.html"), encoding="utf-8").read()
        .replace("{{GETAPP}}", GETAPP).replace("{{DATE}}", td.strftime("%A %d %B %Y").replace(" 0", " ")).replace("{{TABS}}", "".join(tabs)).replace("{{PANELS}}", "".join(panels)))
with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as fh:
    fh.write(home)

# usuń strony wpisów, które już się skończyły albo zostały wycofane
for f in os.listdir(os.path.join(OUT, "e")):
    if f.endswith(".html") and f not in keep:
        os.remove(os.path.join(OUT, "e", f))
for f in used:
    src = os.path.join(photo_dir, "full", f) if os.path.exists(os.path.join(photo_dir, "full", f)) else os.path.join(photo_dir, f)
    shutil.copyfile(src, os.path.join(OUT, "img", f))
print(json.dumps({"pages": len(keep), "images": len(used)}))
