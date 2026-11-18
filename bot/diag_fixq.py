import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
cache = {}
def full(t, p):
    if t not in cache: cache[t] = [x["id"] for x in db.get(t, {"select": "id", "status": "eq.approved", "limit": "9000"})]
    return [i for i in cache[t] if i.startswith(p)]
for t, p in (("events","83f30915"), ("places","c2c946fc"), ("deals","3f06431d")):
    for i in full(t, p): db.update(t, {"id": i}, {"status": "rejected"}); print("L|odrzucony dubel", t, i)
for p, title in (("771ce5b1","Atif Aslam Live"), ("401920fa","Twerk Ladies"), ("8e8d9c87","IIFA Awards"), ("a0fd6936","Kino Band")):
    for i in full("events", p): db.update("events", {"id": i}, {"title": title}); print("L|tytuł", title)
