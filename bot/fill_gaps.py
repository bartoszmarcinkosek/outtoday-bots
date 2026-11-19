"""Jednorazowo: godzina startu i cena dla zatwierdzonych eventów, które zaczynają się w podanym okresie (domyślnie grudzień 2026).
Tylko fakty ze strony oficjalnej / sprzedawcy biletów. Brak pewności = zostaje puste (nie zgadujemy)."""
import os, sys, re, time
sys.path.insert(0, os.path.dirname(__file__))
import run as R
import anthropic

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip(), max_retries=6)
FROM = os.environ.get("FROM") or "2026-12-01"
TO = os.environ.get("TO") or "2026-12-31"
DRY = bool(os.environ.get("DRY"))
ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,price_text,is_free,official_url,url,gaps",
                       "status": "eq.approved", "and": f"(start_date.gte.{FROM},start_date.lte.{TO})", "limit": "5000"})
need = lambda e: (not e.get("start_time")) or (not e.get("price_text") and not e.get("is_free"))
todo = [e for e in ev if need(e) and (e.get("official_url") or e.get("url"))]
print(f"L|eventy {FROM}..{TO}: {len(ev)}, z brakami: {len([e for e in ev if need(e)])}, z linkiem: {len(todo)}")
if DRY:
    for e in todo:
        print("L|  ", e["start_date"], "czas" if not e.get("start_time") else "", "cena" if not (e.get("price_text") or e.get("is_free")) else "", e["title"][:60])
    sys.exit(0)
TOOL = {"name": "facts", "description": "Start time and price of the event, only if written on the page.", "input_schema": {"type": "object", "properties": {
    "same_event": {"type": "boolean", "description": "True only if the page is clearly about THIS event (same name, same date or date range)."},
    "start_time": {"type": ["string", "null"], "description": "Start time as HH:MM 24h, only if written on the page for this date. Doors time does not count unless it is the only time. Null if not written."},
    "end_time": {"type": ["string", "null"], "description": "End time HH:MM 24h if written, else null."},
    "is_free": {"type": ["boolean", "null"], "description": "True only if the page clearly says entry is free. Null if unclear."},
    "price_text": {"type": ["string", "null"], "description": "Short price exactly as the page gives it, in English, e.g. 'From AED 150', 'AED 95 adults, AED 50 kids', 'Free (registration required)'. Null if no price is written. Never estimate."}},
    "required": ["same_event", "start_time", "end_time", "is_free", "price_text"]}}
HHMM = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
usage = {"in": 0, "out": 0}; done = skip = 0
with R.Browser() as br:
    R._BROWSER = br
    for e in todo:
        url = e.get("official_url") or e.get("url")
        ok, why = R.robots_allows(url)
        if not ok: skip += 1; print("L|- robots", e["title"][:50]); continue
        try:
            pg = br.fetch(url)
        except Exception as ex:
            skip += 1; print("L|- fetch", e["title"][:50], type(ex).__name__); continue
        text = (pg["text"] or "")[:14000]
        if pg["status"] >= 400 or len(text) < 200:
            skip += 1; print("L|- page", pg["status"], e["title"][:50]); continue
        r = client.messages.create(model=R.MODEL, max_tokens=300, tools=[TOOL], tool_choice={"type": "tool", "name": "facts"},
            messages=[{"role": "user", "content": f"EVENT: {e['title']} at {e.get('venue') or '?'} ({e['city']}), {e['start_date']}"
                       f"{' to ' + e['end_date'] if e.get('end_date') else ''}.\nUse ONLY facts written in PAGE TEXT. Never guess.\n\nPAGE TEXT:\n{text}"}])
        usage["in"] += r.usage.input_tokens; usage["out"] += r.usage.output_tokens
        d = next((b.input for b in r.content if b.type == "tool_use"), {})
        if not d.get("same_event"):
            skip += 1; print("L|- inny event / brak", e["title"][:50]); continue
        upd, gaps = {}, set(e.get("gaps") or [])
        if not e.get("start_time") and d.get("start_time") and HHMM.match(d["start_time"]):
            upd["start_time"] = d["start_time"]; gaps.discard("start_time")
            if d.get("end_time") and HHMM.match(d["end_time"]):
                upd["end_time"] = d["end_time"]
        if not e.get("price_text") and not e.get("is_free"):
            if d.get("is_free") is True:
                upd["is_free"] = True; upd["price_text"] = (d.get("price_text") or "Free")[:120]; gaps.discard("price")
            elif d.get("price_text") and re.search(r"\d|free", d["price_text"], re.I):
                upd["price_text"] = d["price_text"][:120]; gaps.discard("price")
        if not upd:
            skip += 1; print("L|- brak na stronie", e["title"][:50]); continue
        upd["gaps"] = sorted(gaps)
        db.update("events", {"id": e["id"]}, upd)
        done += 1; print("L|OK", e["start_date"], e["title"][:50], "|", {k: v for k, v in upd.items() if k != "gaps"})
        time.sleep(1)
print(f"L|uzupełnione: {done}, pominięte: {skip}, koszt ok. ${usage['in']/1e6*1 + usage['out']/1e6*5:.2f}")
