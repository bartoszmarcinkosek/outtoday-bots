"""Jednorazowo: krótkie opisy dla eventów od grudnia, które nie mają opisu.
Opis tylko na podstawie strony oficjalnej / sprzedawcy biletów, własnymi słowami. Brak pewności = brak opisu."""
import os, sys, re, json, time
sys.path.insert(0, os.path.dirname(__file__))
import run as R
import anthropic
import cachefix  # noqa: F401  (prompt caching)

db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip(), max_retries=6)
FROM = os.environ.get("FROM", "2026-12-01")
DRY = bool(os.environ.get("DRY"))
TABLE = os.environ.get("TABLE", "events") or "events"  # events | deals | places (27.11.2026: opisy też dla ofert i miejsc)
FIELD = {"events": "description", "deals": "details", "places": "description"}[TABLE]
KIND = {"events": "EVENT", "deals": "OFFER (restaurant/hotel/leisure deal)", "places": "PLACE (venue or attraction)"}[TABLE]
if TABLE == "events":
    ev = db.get("events", {"select": "id,title,venue,city,start_date,end_date,official_url,url,description", "status": "eq.approved",
                           "or": f"(end_date.gte.{FROM},and(end_date.is.null,start_date.gte.{FROM}))", "limit": "8000"})
elif TABLE == "deals":
    ev = [dict(r, start_date="", description=r.get("details")) for r in db.get("deals", {"select": "id,title,venue,city,official_url,details", "status": "eq.approved", "limit": "8000"})]
else:
    ev = [dict(r, title=r["name"], venue=r["name"], start_date="") for r in db.get("places", {"select": "id,name,city,official_url,description", "status": "eq.approved", "limit": "8000"})]
todo = [e for e in ev if len((e.get("description") or "").strip()) < 40 and (e.get("official_url") or e.get("url"))]
print(f"L|{TABLE} bez opisu od {FROM}: {len([e for e in ev if len((e.get('description') or '').strip()) < 30])}, z linkiem: {len(todo)}")
if DRY:
    for e in todo: print("L|  ", e["start_date"], e["title"][:60])
    sys.exit(0)
TOOL = {"name": "describe", "description": "Short description of the event.", "input_schema": {"type": "object", "properties": {
    "found": {"type": "boolean", "description": "True only if the page clearly describes THIS item (event, offer or place)."},
    "description": {"type": ["string", "null"], "description": "1-2 sentences in plain English, in your own words, max 280 characters. Only facts from the page: what it is, who performs or what you can do. No prices, dates, times or hype words. Describe the event itself, never the web page: do not write words like page, listing, post, website or tickets. If the page says almost nothing about the event, set found=false."}},
    "required": ["found", "description"]}}
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
        text = (pg["text"] or "")[:12000]
        if pg["status"] >= 400 or len(text) < 200:
            skip += 1; print("L|- page", pg["status"], e["title"][:50]); continue
        r = client.messages.create(model=R.MODEL, max_tokens=400, tools=[TOOL], tool_choice={"type": "tool", "name": "describe"},
            messages=[{"role": "user", "content": f"{KIND}: {e['title']} at {e.get('venue') or '?'} ({e['city']}) {e.get('start_date') or ''}.\n\nPAGE TEXT:\n{text}"}])
        usage["in"] += r.usage.input_tokens; usage["out"] += r.usage.output_tokens
        d = next((b.input for b in r.content if b.type == "tool_use"), {})
        desc = (d.get("description") or "").strip()
        if not d.get("found") or len(desc) < 30 or re.search(r"\b(page|listing|post|website|ticketing)\b", desc, re.I):
            skip += 1; print("L|- not sure", e["title"][:50]); continue
        db.update(TABLE, {"id": e["id"]}, {FIELD: desc[:400]})
        done += 1; print("L|OK", e["title"][:50], "|", desc[:120])
        time.sleep(1)
print(f"L|opisy: {done}, pominięte: {skip}, koszt ok. ${usage['in']/1e6*1 + usage['out']/1e6*5:.2f}")
