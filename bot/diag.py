"""Diagnostyka: buduje dzisiejszy e-mail bez wysyłania i drukuje sekcję kosztów."""
import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import digest
db = digest.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
data = digest.load(db)
subject, body, text, total = digest.build(data, os.environ["SUPABASE_SECRET_KEY"].strip())
print("SUBJ", subject, "RUNS", len(data["runs"]))
h = body[body.find("Koszty i źródła"):]
print("HEALTH", re.sub(r"<[^>]+>", " ", h)[:800])
