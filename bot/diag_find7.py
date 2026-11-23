"""Tylko odczyt: grupy duplikatów z ostatniej nocnej kontroli – tytuły wszystkich wpisów w grupie."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
runs = db.get("bot_runs", {"select": "summary,started_at", "order": "started_at.desc", "limit": "30"})
rep = next(r["summary"]["report"] for r in runs if (r.get("summary") or {}).get("kind") == "nightly_check")
for d in rep["dupes"]:
    if d["kind"] != "event":
        continue
    rows = db.get("events", {"select": "id,title,start_time,venue,status", "id": "in.(" + ",".join(d["ids"]) + ")"})
    print("F7|" + d["date"] + "|" + " || ".join(f"{r['status'][:3]} {r.get('start_time') or ''} {r['title'][:45]} @{(r.get('venue') or '')[:20]} #{r["id"]}" for r in rows))
