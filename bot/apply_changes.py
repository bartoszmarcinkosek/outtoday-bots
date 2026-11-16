"""Automatyczne przyjmowanie pewnych zmian z bot_changes (żeby e-mail nie był zasypany).

Pewna zmiana = bot znalazł nową wartość na stronie oficjalnej / u sprzedawcy biletów i ma cytat-dowód.
- miejsca i promocje: strona oficjalna (gdy jej nie było), godziny, telefon, cena;
- eventy: cena i godzina rozpoczęcia; miejsce tylko wtedy, gdy było puste.
Zmiany przyjęte automatycznie dostają w evidence przedrostek "[auto] " i trafiają do poniedziałkowej
próbki kontrolnej w e-mailu ("Uzupełnione automatycznie w tym tygodniu"). W e-mailu do decyzji zostają
tylko zmiany bez dowodu albo zmiana miejsca wydarzenia, które już miało miejsce.
"""
from __future__ import annotations

import datetime as dt
import os
import re
import sys

SAFE = {
    "places": {"official_url", "hours_text", "phone", "price_text"},
    "deals": {"official_url", "price_text", "phone", "start_time", "end_time"},
    "events": {"price_text", "start_time", "venue"},
}


def _price_min(text: str | None):
    if not text:
        return None
    m = re.search(r"(?:AED|Dh|dhs?)\s*([0-9][0-9,]*(?:\.[0-9]+)?)|([0-9][0-9,]*(?:\.[0-9]+)?)\s*(?:AED|Dh|dhs?)", text, re.I)
    if not m:
        return None
    try:
        return round(float((m.group(1) or m.group(2)).replace(",", "")))
    except ValueError:
        return None


def apply_safe_changes(db, dry_run: bool = False) -> int:
    rows = db.get("bot_changes", {"select": "*", "handled": "eq.false", "limit": "2000"})
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    n = 0
    for c in rows:
        table, field = c.get("table_name") or "events", c.get("field")
        ev = (c.get("evidence") or "").strip()
        if field not in SAFE.get(table, set()) or not ev or ev.startswith("[auto]"):
            continue
        old, new = c.get("old_value"), c.get("new_value")
        if new in (None, "", "None"):
            continue
        if field == "official_url" and old not in (None, "", "None"):
            continue  # zmiana istniejącego linku: decyduje człowiek
        if table == "events" and field == "venue" and old not in (None, "", "None"):
            continue  # zmiana miejsca istniejącego wydarzenia: decyduje człowiek
        upd: dict = {field: new}
        if field == "start_time":
            m = re.search(r"\b([01]?\d|2[0-3]):([0-5]\d)\b", new)
            if not m:
                continue
            upd[field] = f"{int(m.group(1)):02d}:{m.group(2)}"
        if table == "events" and field == "price_text":
            upd["price_min_aed"] = _price_min(new)
            upd["is_free"] = bool(re.search(r"\bfree\b", new, re.I)) and _price_min(new) in (None, 0)
        if table == "events":
            cur = db.get("events", {"select": "gaps", "id": f"eq.{c['row_id']}"})
            if cur:
                gap = {"price_text": "price", "start_time": "start_time", "venue": "venue"}[field]
                upd["gaps"] = [g for g in (cur[0].get("gaps") or []) if g != gap]
            upd["updated_at"] = now
        elif table == "places":
            upd["verified_at"] = now
        if not dry_run:
            try:
                db.update(table, {"id": c["row_id"]}, upd)
            except RuntimeError as e:
                print(f"  pomijam zmianę {c['id']}: {str(e)[:120]}")
                continue
            db.update("bot_changes", {"id": c["id"]}, {"handled": True, "evidence": f"[auto] {ev}"})
        n += 1
    return n


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    from run import DB
    db = DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    print("Przyjęte automatycznie:", apply_safe_changes(db, dry_run="--dry-run" in sys.argv))
