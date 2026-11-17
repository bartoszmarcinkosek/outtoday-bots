"""Łączy listy hoteli/miejsc z równoległych przebiegów (unia po adresie URL). Użycie: merge_lists.py <nasz_plik> <plik_z_main> <wynik>"""
import json
import sys

ours, theirs, out = sys.argv[1:4]
a = json.load(open(ours, encoding="utf-8"))
b = json.load(open(theirs, encoding="utf-8"))
seen, res = set(), []
for x in b + a:
    k = x["url"].rstrip("/")
    if k not in seen:
        seen.add(k)
        res.append(x)
res.sort(key=lambda h: (h["city"], h["name"]))
json.dump(res, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"{out}: {len(b)} + nowe {len(res) - len(b)} = {len(res)}")
