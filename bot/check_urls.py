"""Sprawdza, czy linki kandydatów (candidates/*.json) działają i czy strona dotyczy tego miejsca.
Nic nie zapisuje. Wypisuje status, adres końcowy i fragmenty z godzinami/cenami."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from run import Browser, robots_allows, norm  # noqa: E402

path = sys.argv[1]
items = json.load(open(path))
items = items.get("places", []) + items.get("deals", []) if isinstance(items, dict) else items
with Browser() as br:
    for it in items:
        name, url = it.get("name") or it.get("title"), it.get("official_url")
        if not url:
            print("CHK", json.dumps({"name": name, "status": "no-url"}))
            continue
        ok, why = robots_allows(url)
        if not ok:
            print("CHK", json.dumps({"name": name, "url": url, "status": "robots", "why": why}))
            continue
        try:
            p = br.fetch(url)
        except Exception as e:  # noqa: BLE001
            print("CHK", json.dumps({"name": name, "url": url, "status": "error", "why": str(e)[:120]}))
            continue
        text = p["text"] or ""
        toks = [t for t in re.findall(r"[a-z]{4,}", norm(name)) if t not in ("dubai", "sharjah", "park", "beach", "museum", "centre", "center")]
        hit = sum(1 for t in toks if t in norm(text))
        snips = []
        for m in re.finditer(r"(?i)(opening hours|open daily|timings|hours|aed|admission|ticket|free entry|free of charge)", text):
            s = text[max(0, m.start() - 60): m.end() + 100].replace("\n", " ")
            if s not in snips:
                snips.append(s)
            if len(snips) >= 4:
                break
        print("CHK", json.dumps({"name": name, "url": url, "status": p["status"], "final": p["final_url"], "chars": len(text),
                                 "name_hit": f"{hit}/{len(toks)}", "snips": snips}, ensure_ascii=False))
