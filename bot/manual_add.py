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
            row.update({"status": "pending", "bot_key": key, "gaps": gaps, "last_seen_at": now,
                        "source_name": e.get("source_name") or "Zrzut ekranu",
                        "evidence": {"page": "zrzut ekranu przesłany przez właściciela", "note": e.get("note") or os.path.basename(path)}})
            db.insert("events", row)
            added += 1
            print(f"+ {row['title']} ({row['start_date']})")
    print(f"Dodane: {added}, już były: {skipped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
