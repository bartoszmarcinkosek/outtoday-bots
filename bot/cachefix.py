"""Prompt caching dla wszystkich botów.

Wystarczy `import cachefix` przed pierwszym wywołaniem API. Łata
Messages.create tak, że stałe części zapytania (tools + system) są
oznaczone cache_control. Kolejne wywołania z tymi samymi regułami w ciągu
5 minut płacą za nie ~10% ceny.

Żeby istniejące liczniki kosztów dalej działały, usage.input_tokens po
odpowiedzi zawiera „równoważnik” ceny: zwykłe tokeny + 1.25x zapis do
cache + 0.1x odczyt z cache.
"""
import copy
import datetime as dt
import os
import sys

import requests
from anthropic.resources.messages import Messages

# ---- Budżet AI (strategia 20.11.2026): twardy limit miesięczny + brak wyszukiwania w sieci bez zgody ----
LIMIT_USD = float(os.environ.get("AI_MONTHLY_LIMIT_USD", "15"))
P_IN, P_OUT, P_SEARCH = 0.10 / 1e6, 0.50 / 1e6, 0.01  # Haiku 5.5; wyszukiwanie 0,01 USD
COST = {"usd": 0.0, "calls": 0, "searches": 0}
_MONTH = {"spent": None}


class SearchDisabled(Exception):
    """Wyszukiwanie w sieci wyłączone (ALLOW_SEARCH=1 tylko po zgodzie właściciela)."""


def _sb():
    url, key = os.environ.get("SUPABASE_URL", "").strip(), os.environ.get("SUPABASE_SECRET_KEY", "").strip()
    return (url, {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}) if url and key else (None, None)


def month_spent() -> float:
    """Suma kosztów AI w bieżącym miesiącu (wiersze bot_runs z summary.kind = 'cost')."""
    url, h = _sb()
    if not url:
        return 0.0
    start = dt.datetime.now(dt.timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    try:
        r = requests.get(f"{url}/rest/v1/bot_runs", headers=h, timeout=30,
                         params={"select": "summary", "finished_at": f"gte.{start}", "summary->>kind": "eq.cost", "limit": "5000"})
        return round(sum(float((x.get("summary") or {}).get("usd") or 0) for x in r.json()), 4)
    except Exception as e:
        print(f"[budżet] nie mogę odczytać kosztów: {e}")
        return 0.0


def guard() -> None:
    """Zatrzymuje skrypt, gdy limit miesięczny jest wyczerpany (sprawdzane raz na uruchomienie)."""
    if _MONTH["spent"] is None:
        _MONTH["spent"] = month_spent()
        print(f"[budżet] koszt AI w tym miesiącu: {_MONTH['spent']:.2f} / {LIMIT_USD:.0f} USD")
    if _MONTH["spent"] + COST["usd"] >= LIMIT_USD:
        raise SystemExit(f"[budżet] limit {LIMIT_USD:.0f} USD w miesiącu osiągnięty – bot zatrzymany")


def add_cost(input_tokens: float = 0, output_tokens: float = 0, searches: int = 0) -> None:
    COST["usd"] += input_tokens * P_IN + output_tokens * P_OUT + searches * P_SEARCH
    COST["calls"] += 1
    COST["searches"] += searches


def _has_search(kwargs) -> bool:
    return any(isinstance(t, dict) and str(t.get("type", "")).startswith("web_search") for t in (kwargs.get("tools") or []))

_orig = Messages.create
STATS = {"cache_write": 0, "cache_read": 0, "plain": 0}


def _mark(kwargs):
    system = kwargs.get("system")
    if isinstance(system, str) and system:
        kwargs["system"] = [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
    elif isinstance(system, list) and system and isinstance(system[-1], dict):
        system = copy.deepcopy(system)
        system[-1].setdefault("cache_control", {"type": "ephemeral"})
        kwargs["system"] = system
    elif kwargs.get("tools"):
        # brak system prompt – cache'ujemy przynajmniej definicje narzędzi
        tools = copy.deepcopy(kwargs["tools"])
        if isinstance(tools[-1], dict):
            tools[-1].setdefault("cache_control", {"type": "ephemeral"})
            kwargs["tools"] = tools


def _create(self, *args, **kwargs):
    if _has_search(kwargs) and os.environ.get("ALLOW_SEARCH") != "1":
        raise SearchDisabled("wyszukiwanie w sieci wyłączone (strategia kosztów)")
    guard()
    if not kwargs.get("stream"):
        _mark(kwargs)
    resp = _orig(self, *args, **kwargs)
    try:
        u = resp.usage
        w = getattr(u, "cache_creation_input_tokens", 0) or 0
        r = getattr(u, "cache_read_input_tokens", 0) or 0
        STATS["cache_write"] += w
        STATS["cache_read"] += r
        STATS["plain"] += u.input_tokens
        stu = getattr(u, "server_tool_use", None)
        add_cost(u.input_tokens + 1.25 * w + 0.1 * r, u.output_tokens, int(getattr(stu, "web_search_requests", 0) or 0))
        if w or r:
            u.input_tokens = u.input_tokens + round(1.25 * w + 0.1 * r)
    except Exception:
        pass
    return resp


Messages.create = _create


def _report():
    if STATS["cache_write"] or STATS["cache_read"]:
        print(f"[cache] zapis {STATS['cache_write']}, odczyt {STATS['cache_read']}, zwykłe {STATS['plain']} tokenów")
    if COST["calls"]:
        script = os.path.basename(sys.argv[0] or "?")
        print(f"[budżet] koszt tego uruchomienia ({script}): {COST['usd']:.3f} USD, zapytań {COST['calls']}, wyszukiwań {COST['searches']}")
        url, h = _sb()
        if url:
            try:
                requests.post(f"{url}/rest/v1/bot_runs", headers=h, timeout=30, json={
                    "dry_run": False, "finished_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                    "summary": {"kind": "cost", "script": script, "usd": round(COST["usd"], 4),
                                "calls": COST["calls"], "searches": COST["searches"]}})
            except Exception as e:
                print(f"[budżet] nie zapisałem kosztu: {e}")


import atexit  # noqa: E402

atexit.register(_report)
