"""Konta Instagram już sprawdzone i odrzucone (audit/ig_rejected.txt) – żeby żadne narzędzie nie pytało o nie drugi raz.

Format pliku: nazwa | powód | data.  Wpis przestaje obowiązywać po 180 dniach (konto mogło powstać albo ożyć).
"""
from __future__ import annotations

import datetime as dt
import os

F = os.path.join(os.path.dirname(__file__), "..", "audit", "ig_rejected.txt")
DAYS = 180


SOFT = ("brak UAE", "wygląda na konto osoby")  # ocena automatu po opisie – ręcznie wskazane konto wolno sprawdzić jeszcze raz


def load(hard_only: bool = False) -> set[str]:
    out, today = set(), dt.date.today()
    try:
        for l in open(F, encoding="utf-8"):
            p = [x.strip() for x in l.split("|")]
            if l.startswith("#") or not p[0]:
                continue
            try:
                old = (today - dt.date.fromisoformat(p[2])).days > DAYS
            except Exception:
                old = False
            if hard_only and len(p) > 1 and p[1].startswith(SOFT):
                continue
            if not old:
                out.add(p[0].lower())
    except FileNotFoundError:
        pass
    return out


def add(rows) -> int:
    """rows: [(nazwa, powód)] – dopisuje tylko nowe."""
    have, new = load(), {}
    for u, why in rows:
        u = u.strip().lstrip("@").lower()
        if u and u not in have and u not in new:
            new[u] = " ".join(str(why).replace("|", "/").split())[:90]
    if new:
        head = not os.path.exists(F)
        with open(F, "a", encoding="utf-8") as f:
            if head:
                f.write("# nazwa | powód | data sprawdzenia – tych nazw nie sprawdzamy ponownie przez 180 dni\n")
            for u, why in new.items():
                f.write(f"{u} | {why} | {dt.date.today()}\n")
    return len(new)
