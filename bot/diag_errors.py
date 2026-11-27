"""Tylko odczyt: automatyczne zgłoszenia błędów z apki (suggestions, tytuł "AppError: ...") z ostatnich HOURS godzin (domyślnie 26).
Linie: ER|ile razy|rodzaj i treść|przykładowe środowisko|stos (skrót) ; EZ| podsumowanie."""
import collections, datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
since = (dt.datetime.utcnow() - dt.timedelta(hours=int(os.environ.get("HOURS", "26")))).strftime("%Y-%m-%dT%H:%M:%S")
rows = db.get("suggestions", {"select": "title,note,created_at", "title": "like.AppError:*", "created_at": f"gte.{since}", "limit": "1000"})
g = collections.defaultdict(list)
for r in rows:
    g[r["title"]].append(r)
print(f"EZ|since {since}|zgłoszeń {len(rows)}|różnych błędów {len(g)}")
for t, rs in sorted(g.items(), key=lambda x: -len(x[1])):
    note = (rs[0].get("note") or "").replace("\n", " ⏎ ")
    print(f"ER|{len(rs)}|{t}|{note[:700]}")
