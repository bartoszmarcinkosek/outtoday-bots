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

from anthropic.resources.messages import Messages

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
        if w or r:
            u.input_tokens = u.input_tokens + round(1.25 * w + 0.1 * r)
    except Exception:
        pass
    return resp


Messages.create = _create


def _report():
    if STATS["cache_write"] or STATS["cache_read"]:
        print(f"[cache] zapis {STATS['cache_write']}, odczyt {STATS['cache_read']}, zwykłe {STATS['plain']} tokenów")


import atexit  # noqa: E402

atexit.register(_report)
