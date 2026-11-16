"""Wpisy ze zrzutów ekranu (np. z grup WhatsApp, Instagrama) przesłanych w czacie.
Claude zapisuje je w manual/*.json; ten skrypt dodaje je do bazy jako pending (trafiają do porannego e-maila).
Ten sam wpis nie zostanie dodany dwa razy."""
import datetime as dt
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402

EVENT_FIELDS = ("title", "category", "start_date", "end_date", "start_time", "end_time", "venue", "city", "price_text",
                "price_min_aed", "is_free", "kid_friendly", "registration_required", "description", "official_url", "url")


def main() -> int:
    db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    added = skipped = 0
    for path in sorted(glob.glob("manual/*.json")):
        data = json.load(open(path, encoding="utf-8"))
        for e in data.get("events", []):
            key = "manual:" + hashlib.sha1(f"{R.norm(e['title'])}|{e['start_date']}|{R.norm(e.get('venue'))}".encode()).hexdigest()[:20]
            if db.get("events", {"select": "id", "bot_key": f"eq.{key}"}):
                skipped += 1
                continue
            row = {k: e[k] for k in EVENT_FIELDS if k in e and e[k] not in (None, "")}
            row.setdefault("city", "Abu Dhabi")
            row.setdefault("category", "community")
            gaps = [g for g, f in (("start_time", "start_time"), ("venue", "venue"), ("price", "price_text")) if not row.get(f)]
            if row.get("is_free"):
                gaps = [g for g in gaps if g != "price"]
            st = "approved" if e.get("status") == "approved" else "pending"
            if st == "approved":
                row["verified_at"] = now
            row.update({"status": st, "bot_key": key, "gaps": gaps, "last_seen_at": now,
                        "source_name": e.get("source_name") or "Zrzut ekranu",
                        "evidence": {"page": "zrzut ekranu przesłany przez właściciela", "note": e.get("note") or os.path.basename(path)}})
            db.insert("events", row)
            added += 1
            print(f"+ {row['title']} ({row['start_date']})")
        for d in data.get("deals", []):
            if db.get("deals", {"select": "id", "title": f"eq.{d['title']}", "venue": f"eq.{d.get('venue')}"}):
                skipped += 1
                continue
            row = {k: d[k] for k in ("title", "details", "venue", "area", "city", "days_of_week", "start_time", "end_time",
                                     "price_text", "valid_until", "official_url", "deal_type", "ladies_only", "kid_friendly",
                                     "pet_friendly") if k in d and d[k] not in (None, "")}
            row.update({"status": "approved" if d.get("status") == "approved" else "pending",
                        "source_name": d.get("source_name") or "Zrzut ekranu"})
            db.insert("deals", row)
            added += 1
            print(f"+ deal: {row['title']}")
        for pl in data.get("places", []):
            if db.get("places", {"select": "id", "name": f"eq.{pl['name']}"}):
                skipped += 1
                continue
            row = {k: pl[k] for k in ("name", "description", "category", "area", "city", "hours_text", "price_text",
                                      "is_free", "official_url", "kid_friendly", "is_indoor") if k in pl and pl[k] not in (None, "")}
            row.update({"status": "approved" if pl.get("status") == "approved" else "pending",
                        "source_name": pl.get("source_name") or "Zrzut ekranu"})
            db.insert("places", row)
            added += 1
            print(f"+ place: {row['name']}")
        for r in data.get("approve", []):
            q = {"select": "id,title,status,gaps", "title": f"ilike.{r['title']}"}
            if r.get("start_date"):
                q["start_date"] = f"eq.{r['start_date']}"
            rows = db.get("events", q)
            # "set": poprawki pól sprawdzone na oficjalnej stronie (np. venue "Various venues across Sharjah").
            fix = {k: v for k, v in (r.get("set") or {}).items() if k in ("venue", "price_text", "is_free", "start_time", "end_time", "description", "official_url", "category")}
            for row in rows:
                if row["status"] != "approved" or fix:
                    upd = {"status": "approved", "verified_at": now, "updated_at": now, **fix}
                    if fix:
                        filled = {"venue" if "venue" in fix else None, "price" if ("price_text" in fix or "is_free" in fix) else None,
                                  "start_time" if "start_time" in fix else None}
                        upd["gaps"] = [g for g in (row.get("gaps") or []) if g not in filled]
                    db.update("events", {"id": row["id"]}, upd)
                    print(f"✓ zatwierdzone: {row['title']} ({r.get('start_date', '')}) {fix or ''}")
        for r in data.get("reject", []):
            rows = db.get("events", {"select": "id,title,status", "title": f"ilike.{r['title']}", "start_date": f"eq.{r['start_date']}"})
            for row in rows:
                if row["status"] != "rejected":
                    db.update("events", {"id": row["id"]}, {"status": "rejected", "updated_at": now})
                    print(f"- odrzucone: {row['title']} ({r['start_date']})")
        # "update_deals": [{"title":..., "venue":..., "set": {...}}] – poprawki z oficjalnej strony.
        for r in data.get("update_deals", []):
            fix = {k: v for k, v in (r.get("set") or {}).items() if k in ("price_text", "details", "official_url", "start_time", "end_time", "days_of_week")}
            for row in db.get("deals", {"select": "id,title", "title": f"eq.{r['title']}", "venue": f"eq.{r['venue']}"}):
                db.update("deals", {"id": row["id"]}, fix)
                print(f"~ deal poprawiony: {row['title']} {fix}")
        # "reject_deals": [{"title":..., "venue":...}] – np. duplikaty.
        for r in data.get("reject_deals", []):
            rows = db.get("deals", {"select": "id,title,status", "title": f"eq.{r['title']}", "venue": f"eq.{r['venue']}"})
            for row in rows:
                if row["status"] != "rejected":
                    db.update("deals", {"id": row["id"]}, {"status": "rejected"})
                    print(f"- deal ukryty: {row['title']}")
        # "reject_places": lista id miejsc do ukrycia (np. zwykłe centra handlowe).
        for pid in data.get("reject_places", []):
            rows = db.get("places", {"select": "id,name,status", "id": f"eq.{pid}"})
            for row in rows:
                if row["status"] != "rejected":
                    db.update("places", {"id": row["id"]}, {"status": "rejected"})
                    print(f"- miejsce ukryte: {row['name']}")
        # "update_places": [{"name":..., "city":..., "set": {...}}] – poprawki ceny/godzin/telefonu
        for r in data.get("update_places", []):
            fix = {k: v for k, v in (r.get("set") or {}).items() if k in ("price_text", "hours_text", "is_free", "phone", "official_url")}
            q = {"select": "id,name", "name": f"eq.{r['name']}"}
            if r.get("city"):
                q["city"] = f"eq.{r['city']}"
            for row in db.get("places", q):
                db.update("places", {"id": row["id"]}, fix)
                print(f"~ miejsce poprawione: {row['name']} {fix}")
    print(f"Dodane: {added}, już były: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
