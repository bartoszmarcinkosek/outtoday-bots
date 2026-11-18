import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
for pat in ("*virtual-exhibitions*", "*adipec-2026*", "*the-arts-center.html*"):
    for e in db.get("events", {"select": "id,title,official_url", "official_url": f"like.{pat}"}):
        db.update("events", {"id": e["id"]}, {"official_url": None}); print("L|cofnięte", e["title"])
