"""Eksport wszystkich tabel OutToday do jednego pliku JSON (kopia zapasowa)."""
import json, os, sys, requests
URL = os.environ["SUPABASE_URL"].strip().rstrip("/")
KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
TABLES = ["events", "places", "deals", "bot_pages", "bot_changes", "bot_runs"]
out = {}
for t in TABLES:
    rows, start = [], 0
    while True:
        r = requests.get(f"{URL}/rest/v1/{t}", headers={"apikey": KEY, "Range-Unit": "items", "Range": f"{start}-{start + 999}"},
                         params={"select": "*"}, timeout=60)
        if r.status_code not in (200, 206):
            print(f"{t}: błąd {r.status_code} {r.text[:200]}"); break
        batch = r.json(); rows += batch
        if len(batch) < 1000: break
        start += 1000
    out[t] = rows
    print(f"{t}: {len(rows)}")
json.dump(out, open(sys.argv[1], "w"), ensure_ascii=False)
