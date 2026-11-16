import os, re, sys, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("events", {"select": "id,title,start_date,venue,status,source_name,bot_key", "source_name": "ilike.*meetup*", "status": "eq.pending", "order": "start_date"})
BAD = re.compile(r"silent reading|speed|dating|singles|mingle|networking|investor|founder|online|webinar|zoom|virtual")
VAGUE = re.compile(r"^(dubai[ ,]*)+(united arab emirates)?$")
seen = collections.Counter(); rej = keep = 0
for r in rows:
    t = R.norm(r["title"]); v = R.norm(r["venue"] or "")
    seen[t] += 1
    bad = BAD.search(t) or not v or VAGUE.match(v) or seen[t] > 3
    if bad:
        db.update("events", {"id": r["id"]}, {"status": "rejected"}); rej += 1
    else:
        keep += 1; print("KEEP", r["start_date"], "|", r["title"], "|", r["venue"])
print("MEETUP pending:", len(rows), "rejected:", rej, "kept:", keep)
