"""Test klucza Unsplash: jedno wyszukiwanie, bez pobierania zdjęć."""
import os, requests
k = os.environ.get("UNSPLASH_KEY", "")
print("US|key present", bool(k), "len", len(k))
if k:
    r = requests.get("https://api.unsplash.com/search/photos",
                     params={"query": "camel race", "per_page": 3},
                     headers={"Authorization": f"Client-ID {k}", "Accept-Version": "v1"}, timeout=20)
    print("US|http", r.status_code, "remaining", r.headers.get("X-Ratelimit-Remaining"), "limit", r.headers.get("X-Ratelimit-Limit"))
    if r.ok:
        j = r.json(); print("US|total", j.get("total"))
        for p in j.get("results", []):
            print("US|", p["id"], p["user"]["name"], (p.get("alt_description") or "")[:60])
