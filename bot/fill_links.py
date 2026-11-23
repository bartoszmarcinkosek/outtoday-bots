"""Jednorazowo: szuka stron oficjalnych dla nadchodzących eventów bez dobrego linku.
Wpisuje link sam tylko gdy strona działa i wymienia tytuł eventu; resztę daje jako propozycję do bot_changes."""
import os, sys, re, time
from urllib.parse import urlparse
sys.path.insert(0, os.path.dirname(__file__))
import run as R
import verify as V
import anthropic
import cachefix  # noqa: F401  (prompt caching)

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip(), max_retries=6)
LIMIT = int(os.environ.get("LIMIT", "160"))
ti = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,title,venue,area,city,start_date,end_date,official_url,url,description,source_name", "status": "eq.approved",
                       "or": f"(end_date.gte.{ti},and(end_date.is.null,start_date.gte.{ti}))", "limit": "8000"})
def generic(u):
    p = urlparse(u or "")
    return (not u) or p.path in ("", "/") or bool(re.search(r"/(event/list|shows|festival|events?|whats-on)/?$", p.path or ""))
bad = [e for e in ev if generic(e.get("official_url")) and generic(e.get("url"))]
bad.sort(key=lambda e: e["start_date"])
if os.environ.get("ONLY") == "national":
    rx = re.compile(r"national day|eid al etihad|eid al-etihad|etihad day|union day|spirit of the union|عيد الاتحاد|\b55\b|\b55th\b", re.I)
    bad = [e for e in bad if rx.search((e["title"] or "") + " " + (e.get("description") or "")) and e["start_date"] <= "2026-12-07"]
    for e in bad: print(f"L|  * {e['start_date']} {e['title'][:70]}")
if os.environ.get("ONLY") == "december":
    bad = [e for e in bad if "2026-12-01" <= e["start_date"] <= "2026-12-31" and "platinumlist" not in (e.get("source_name") or "").lower()]
if os.environ.get("DRY"): print(f"L|DRY {len(bad)}"); sys.exit(0)
if os.environ.get("FREE"):
    # bez AI: otwiera stronę źródła eventu i bierze link, którego tekst pasuje do tytułu
    pages, fixed = {}, 0
    with R.Browser() as br:
        for e in bad:
            src = e.get("url") if not generic(e.get("url")) else None
            src = src or db.get("events", {"select": "source_url", "id": f"eq.{e['id']}"})[0].get("source_url")
            if not src:
                continue
            if src not in pages:
                try:
                    pg = br.fetch(src); pages[src] = (pg["links"], pg["final_url"])
                except Exception:
                    pages[src] = ([], src)
                time.sleep(1)
            links, final = pages[src]
            u = R.link_for_title(e["title"], links, final)
            if u and not generic(u):
                db.update("events", {"id": e["id"]}, {"official_url": u}); fixed += 1
                print(f"L|OK {e['title'][:60]} -> {u}")
    print(f"L|FREE poprawione {fixed} z {len(bad)} (stron {len(pages)}), koszt $0")
    sys.exit(0)
print(f"L|do sprawdzenia {len(bad)}")
STOP = {"the", "and", "with", "for", "live", "abu", "dhabi", "dubai", "uae", "2026", "2027", "edition", "festival", "event"}
usage = {"input": 0, "output": 0, "calls": 0, "searches": 0}
open_ch = {(c["row_id"], c["new_value"]) for c in db.get("bot_changes", {"select": "row_id,new_value", "field": "eq.official_url", "handled": "eq.false", "limit": "5000"})}
auto = prop = none = 0
with R.Browser() as br:
    R._BROWSER = br
    for e in bad[:LIMIT]:
        url, why = V.find_official_url(client, "events", e, usage)
        if not url:
            none += 1; print(f"L|-  {e['title'][:60]} | {why[:80]}"); continue
        if generic(url):
            none += 1; print(f"L|-  {e['title'][:60]} | ogólna strona {url}"); continue
        ok = False
        try:
            pg = br.fetch(url)
            txt = R.norm(pg["text"] or "")
            words = [w for w in R._tokens(e["title"]) if len(w) > 3 and w not in STOP]
            hit = sum(1 for w in words if w in txt)
            ok = pg["status"] < 400 and len(txt) > 200 and words and hit / len(words) >= 0.6 and not generic(pg["final_url"])
        except Exception as ex:
            why = f"{why} / fetch {type(ex).__name__}"
        if ok:
            db.update("events", {"id": e["id"]}, {"official_url": url})
            auto += 1; print(f"L|OK {e['title'][:60]} -> {url}")
        elif (e["id"], url) not in open_ch:
            db.insert("bot_changes", {"table_name": "events", "row_id": e["id"], "field": "official_url",
                                      "old_value": e.get("official_url"), "new_value": url, "evidence": why[:300], "source_url": url})
            prop += 1; print(f"L|?  {e['title'][:60]} -> {url}")
        time.sleep(1)
cost = usage["input"] / 1e6 * 1 + usage["output"] / 1e6 * 5 + usage["searches"] * 0.01
print(f"L|wpisane {auto}, propozycje {prop}, brak {none}; wyszukiwań {usage['searches']}, koszt ok. ${cost:.2f}")
