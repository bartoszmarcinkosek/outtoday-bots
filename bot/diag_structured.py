"""Tylko odczyt: które źródła podają wydarzenia w gotowej postaci (JSON-LD Event, plik ICS, RSS) – do czytania bez AI.
Linie SD|id|miasto|jsonld_events|ics|rss|status|url ; SZ| podsumowanie."""
import os, sys, re, json, glob
sys.path.insert(0, os.path.dirname(__file__))
import requests
import run as R

def count_events(o):
    n = 0
    if isinstance(o, list):
        return sum(count_events(x) for x in o)
    if isinstance(o, dict):
        t = o.get("@type")
        ts = t if isinstance(t, list) else [t]
        if any(isinstance(x, str) and x.endswith("Event") for x in ts) and o.get("startDate"):
            n += 1
        for v in o.values():
            if isinstance(v, (list, dict)):
                n += count_events(v)
    return n

srcs = []
for f in sorted(glob.glob(os.path.join(os.path.dirname(__file__), "..", "sources", "*.json"))):
    d = json.load(open(f))
    if isinstance(d, dict) and isinstance(d.get("sources"), list):
        srcs += d["sources"]
tot = {"jsonld": 0, "ics": 0, "rss": 0, "n": 0}
for s in srcs:
    for url in (s.get("urls") or [])[:1]:
        tot["n"] += 1
        try:
            ok, why = R.robots_allows(url)
            if not ok:
                print(f"SD|{s['id']}|{s.get('city')}|-|-|-|{why}|{url}"); continue
            r = requests.get(url, headers={"User-Agent": R.USER_AGENT}, timeout=25)
            h = r.text
            n = 0
            for m in re.finditer(r'<script[^>]+application/ld\+json[^>]*>(.*?)</script>', h, re.S | re.I):
                try:
                    n += count_events(json.loads(m.group(1).strip()))
                except Exception:
                    pass
            ics = len(re.findall(r'href="[^"]+\.ics[^"]*"|webcal://|ical=1|/ical/?"', h, re.I))
            rss = len(re.findall(r'type="application/(rss|atom)\+xml"', h, re.I))
            tot["jsonld"] += n > 0; tot["ics"] += ics > 0; tot["rss"] += rss > 0
            if n or ics or rss:
                print(f"SD|{s['id']}|{s.get('city')}|{n}|{ics}|{rss}|HTTP {r.status_code}|{url}")
        except Exception as e:
            print(f"SD|{s['id']}|{s.get('city')}|-|-|-|{type(e).__name__}|{url}")
print(f"SZ|sources {tot['n']}|with JSON-LD events {tot['jsonld']}|with ICS {tot['ics']}|with RSS {tot['rss']}")
