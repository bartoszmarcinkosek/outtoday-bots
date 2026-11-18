import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
D = {
 "Live Entertainment at Fresca Pool Bar": "Live music and entertainment by the pool at Fresca Pool Bar, Al Hamra Village Hotel.",
 "Yasalam After-Race Concert: Kings of Leon": "American rock band Kings of Leon headline a Yasalam after-race concert during the Abu Dhabi Grand Prix weekend.",
 "Formula 1 Etihad Airways Abu Dhabi Grand Prix": "The final race of the Formula 1 season at Yas Marina Circuit, with practice, qualifying and the Grand Prix across the weekend.",
 "On Track: Season Finale Abu Dhabi 2026": None,
 "Comedy Box Office By Jaspreet Singh in Dubai": "A stand-up comedy show by Indian comedian Jaspreet Singh.",
 "Elissa Live in Abu Dhabi": "Lebanese pop star Elissa performs her best-known Arabic hits live.",
 "Ebru Gundes": "Turkish singer Ebru Gündeş performs live in concert.",
 "Abu Dhabi Comedy Season: Whitney Cummings": "American stand-up comedian Whitney Cummings performs a live show as part of the Abu Dhabi Comedy Season.",
 "Abu Dhabi Comedy Season: Paul Smith": "Liverpool stand-up comedian Paul Smith performs a live show as part of the Abu Dhabi Comedy Season.",
 "Harry Potter Film Concert Series": "A Harry Potter film is screened on a big screen while a live orchestra plays the score.",
 "Charlie and the Chocolate Factory: The Musical": "The stage musical of Roald Dahl's story about Charlie Bucket and Willy Wonka's chocolate factory.",
 "CATS The Musical": "Andrew Lloyd Webber's musical about a tribe of cats, with songs including \"Memory\".",
 "Riverdance": "The Irish dance show with fast-paced step dancing and live music.",
}
ti = R.today_uae().isoformat()
for t, d in D.items():
    for e in db.get("events", {"select": "id,title,description", "status": "eq.approved", "title": f"eq.{t}", "start_date": "gte.2026-12-01"}):
        if re.search(r"page|listing|post|upgrade|ticketing", e.get("description") or "", re.I):
            db.update("events", {"id": e["id"]}, {"description": d}); print("L|fixed", t)
