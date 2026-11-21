"""Poprawa wielkości liter w tytułach BEZ AI (koszt 0 USD). Uruchamiane co noc z nightly_check.py i ręcznie.
- tytuł zaczynający się małą literą -> pierwsza litera wielka ("marckinchen at ..." -> "Marckinchen at ...");
  wyjątek: nazwy typu iPhone/eBay (druga litera wielka) zostają;
- tytuł pisany WIELKIMI LITERAMI -> normalne litery; krótkie skróty (do 4 liter: UAE, DJ, NYE, RAK) zostają wielkie.
DRY=1 tylko wypisuje zmiany."""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402

SMALL = {"a", "an", "and", "at", "by", "for", "in", "of", "on", "or", "the", "to", "with", "x", "vs", "de", "la", "el", "al"}
KEEP_UPPER = {"II", "III", "IV", "VIP", "UAE", "DJ", "NYE", "RAK", "UAQ", "DXB", "AUH", "F1", "MMA", "UFC", "WWE", "NBA", "ADNOC", "ADNEC", "DIFC", "JBR", "JLT", "QE2", "UK", "USA", "EDM", "R&B", "BBQ", "AED"}


def _caps(t: str) -> bool:
    w = re.findall(r"[A-Za-z]{3,}", t)
    return len(w) >= 2 and sum(x.isupper() for x in w) / len(w) >= 0.6


def _word(w: str, first: bool) -> str:
    core = re.sub(r"[^A-Za-z0-9&]", "", w)
    if core.upper() in KEEP_UPPER or (core.isupper() and len(core) <= 3 and core.isalpha() and core.lower() not in SMALL):
        return w
    low = w.lower()
    if not first and core.lower() in SMALL:
        return low
    return re.sub(r"[a-z]", lambda m: m.group(0).upper(), low, count=1)


def fixed(t: str | None) -> str | None:
    if not t or not t.strip():
        return None
    new = t
    if _caps(t):
        parts = re.split(r"(\s+)", t)
        out, first = [], True
        for p in parts:
            if p.strip():
                out.append(_word(p, first))
                first = False
            else:
                out.append(p)
        new = "".join(out)
    m = re.search(r"[A-Za-z]", new)
    if m and new[m.start()].islower() and not (m.start() + 1 < len(new) and new[m.start() + 1].isupper()):
        new = new[: m.start()] + new[m.start()].upper() + new[m.start() + 1:]
    return new if new != t else None


def run(db, dry: bool = False) -> list[str]:
    changes = []
    for table, col in (("events", "title"), ("places", "name"), ("deals", "title")):
        rows = db.get(table, {"select": f"id,{col}", "status": "in.(approved,pending)", "limit": "20000"})
        for r in rows:
            n = fixed(r.get(col))
            if n:
                changes.append(f"{table}: {r[col]!r} -> {n!r}")
                if not dry:
                    db.update(table, {"id": r["id"]}, {col: n})
    return changes


if __name__ == "__main__":
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    ch = run(db, dry=bool(os.environ.get("DRY")))
    print(f"T|poprawione tytuły: {len(ch)}")
    for c in ch:
        print("T|" + c)
