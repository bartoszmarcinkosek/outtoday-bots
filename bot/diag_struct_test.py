"""Próba: czy przeglądarka bota odczytuje dane strukturalne (JSON-LD) i czy ocena źródeł liczy się bez błędu."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import run as R
import instagram  # noqa: F401  (sprawdzenie, że moduł się ładuje)
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
print("ST|probation", len(db.probation()))
print("ST|guard", db._guard("events", {"status": "approved", "source_name": "Eventbrite", "evidence": {"auto": True}, "verified_at": "x"}))
print("ST|guard-ok", db._guard("events", {"status": "approved", "source_name": "Alserkal Avenue"})["status"])
with R.Browser() as br:
    for u in ("https://bluewatersdubai.ae/en/whats-on/events", "https://www.ibnbattutamall.com/events"):
        p = br.fetch(u)
        print("ST|", u, p["status"], len(p.get("structured") or []), (p.get("structured") or [None])[0])
