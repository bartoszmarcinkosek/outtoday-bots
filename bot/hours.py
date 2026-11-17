"""OutToday: zamienia tekst godzin otwarcia miejsc (places.hours_text) na tabelę dni i godzin (places.hours).

Format: {"0": [["10:00","22:00"]], ..., "6": [...]}, 0 = niedziela. Zamknięcie po północy, np. ["18:00","02:00"].
Pusty słownik {} = nie da się odczytać (np. "Best at dawn"); apka wtedy nie pokazuje "Open now".
Godziny ramadanowe i sezonowe wyjątki są pomijane (bierzemy zwykły tydzień).

Uruchomienie: python bot/hours.py [--all] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402
import hotels as H  # noqa: E402

TOOL = {
    "name": "report_hours",
    "description": "Weekly opening hours.",
    "input_schema": {"type": "object", "properties": {"items": {"type": "array", "items": {"type": "object", "properties": {
        "id": {"type": "string"},
        "readable": {"type": "boolean", "description": "false if the text does not state regular opening hours"},
        "always_open": {"type": "boolean"},
        "days": {"type": "object", "description": "Keys are day names Sun, Mon, Tue, Wed, Thu, Fri, Sat. Value: list of [open, close] in HH:MM 24h. Omit closed days.",
                 "properties": {d: {"type": "array", "items": {"type": "array", "items": {"type": "string"}}} for d in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]}},
    }, "required": ["id", "readable", "always_open", "days"]}}}, "required": ["items"]},
}
RULES = """Convert each opening-hours text of a UAE venue into a regular weekly schedule.
- Use only what the text says. Ignore Ramadan, holiday and seasonal exceptions, last-entry times, tour slots and happy hours.
- "midnight"/"12 AM" as closing = "24:00". Closing after midnight: e.g. ["18:00","02:00"].
- Write out every open day separately; check each day name carefully (Sat to Thu = Sat, Sun, Mon, Tue, Wed, Thu).
- "Fri and Sat until midnight" after "Sun to Thu 10:00 to 22:00" means Fri/Sat 10:00 to 24:00.
- If the text has no regular hours (e.g. "Best at dawn", "Book online", "Session times vary", "Currently closed",
  only one day like "OPEN TODAY", or only a closing time), set readable=false.
- "Open 24 hours"/"Always open": always_open=true."""
TIME = re.compile(r"^([01]\d|2[0-4]):[0-5]\d$")


def clean(it: dict) -> dict:
    if it.get("always_open"):
        return {str(d): [["00:00", "24:00"]] for d in range(7)}
    if not it.get("readable"):
        return {}
    out = {}
    names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    for name, spans in (it.get("days") or {}).items():
        if name not in names or not isinstance(spans, list):
            continue
        k = str(names.index(name))
        good = [[a, b] for a, b in (s for s in spans if isinstance(s, list) and len(s) == 2) if TIME.match(a) and TIME.match(b)]
        if good:
            out[k] = good
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true", help="także miejsca, które mają już tabelę")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    q = {"select": "id,name,hours_text", "hours_text": "not.is.null", "limit": "5000"}
    if not a.all:
        q["hours"] = "is.null"
    rows = [r for r in db.get("places", q) if (r.get("hours_text") or "").strip()]
    print(f"Miejsc do przeliczenia: {len(rows)}")
    client, usage = H.client_usage()
    done = 0
    for i in range(0, len(rows), 10):
        batch = rows[i:i + 10]
        msg = "\n".join(json.dumps({"id": r["id"], "text": r["hours_text"][:400]}, ensure_ascii=False) for r in batch)
        resp = client.messages.create(model=R.MODEL, max_tokens=8000, system=RULES, tools=[TOOL],
                                      tool_choice={"type": "tool", "name": "report_hours"},
                                      messages=[{"role": "user", "content": msg}])
        H.add_usage(usage, resp)
        items = next((b.input.get("items") or [] for b in resp.content if b.type == "tool_use"), [])
        ids = {r["id"]: r for r in batch}
        for it in items:
            if not isinstance(it, dict) or it.get("id") not in ids:
                continue
            h = clean(it)
            print(f"{ids[it['id']]['name'][:40]:40} | {ids[it['id']]['hours_text'][:60]:60} -> {json.dumps({["Sun","Mon","Tue","Wed","Thu","Fri","Sat"][int(k)]: v for k, v in h.items()})[:220]}")
            if not a.dry_run:
                db.update("places", {"id": it["id"]}, {"hours": h})
            done += 1
    print(f"Zapisano: {done}. Koszt AI ≈ ${H.cost(usage):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
