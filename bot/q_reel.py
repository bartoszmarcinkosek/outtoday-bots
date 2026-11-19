import os, re, json
ROOT = os.path.join(os.path.dirname(__file__), "..")
import run as R
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



db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"])
rows = db.get("events", {"select": "id,title,venue,area,city,category,start_date,end_date,start_time,end_time,price_text,is_free,description,kid_friendly",
  "status": "eq.approved", "city": "eq.Abu Dhabi", "start_date": "lte.2026-11-22",
  "or": "(end_date.gte.2026-11-20,and(end_date.is.null,start_date.gte.2026-11-20))", "limit": "500"})
for x in rows:
    x["photo"] = photo_for("event", "event:" + x["id"], x["title"], f"{x['title']} {x.get('venue') or ''} {x.get('area') or ''}", x.get("category") or "", "Abu Dhabi")
    x["description"] = (x.get("description") or "")[:140]
    print("EV " + json.dumps(x, ensure_ascii=False))
