import os, re, collections, run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
ev = db.get("events", {"select": "title,venue,city", "status": "eq.approved", "start_date": "gte.2026-11-01", "limit": "8000"})
pl = db.get("places", {"select": "name,area,city", "status": "eq.approved", "limit": "5000"})
dl = db.get("deals", {"select": "venue,city", "status": "eq.approved", "limit": "5000"})
LM = {"burj khalifa": r"burj khalifa|at the top|dubai fountain|downtown dubai", "burj al arab": r"burj al arab",
 "louvre": r"louvre", "miracle garden": r"miracle garden", "grand mosque": r"grand mosque|sheikh zayed mosque",
 "etihad arena": r"etihad arena", "coca-cola arena": r"coca[- ]cola arena", "dubai opera": r"dubai opera",
 "global village": r"global village", "museum of the future": r"museum of the future", "expo city": r"expo city|al wasl",
 "qasr al watan": r"qasr al watan", "ain dubai": r"ain dubai|bluewaters", "dubai frame": r"dubai frame",
 "yas marina circuit": r"yas marina circuit|yas marina", "ferrari world": r"ferrari world", "warner bros": r"warner",
 "seaworld": r"seaworld", "atlantis": r"atlantis", "palm jumeirah": r"palm jumeirah", "jebel jais": r"jebel jais",
 "hatta": r"hatta", "al qasba": r"al qasba", "sharjah aquarium": r"sharjah aquarium", "manarat": r"manarat",
 "saadiyat": r"saadiyat", "corniche": r"corniche", "kite beach": r"kite beach", "la mer": r"la mer", "jbr": r"\bjbr\b|the beach jbr",
 "abu dhabi cruise/marina mall": r"marina mall", "zayed national museum": r"zayed national museum", "teamlab": r"teamlab",
 "nyuad arts center": r"arts center|nyuad|nyu abu dhabi", "cultural foundation": r"cultural foundation", "al hosn": r"al hosn",
 "dubai creek / al seef": r"al seef|dubai creek|creek harbour", "madinat jumeirah": r"madinat", "rak expo/night market": r"rak exhibition|rak expo"}
c = collections.Counter()
for rows, f in ((ev, "title venue"), (pl, "name area"), (dl, "venue")):
    for r in rows:
        txt = " ".join(str(r.get(k) or "") for k in f.split())
        for k, rx in LM.items():
            if re.search(rx, txt, re.I): c[k] += 1
for k, n in c.most_common(): print("LM |", n, k)
