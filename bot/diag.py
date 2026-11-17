import os, sys, re, itertools, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SECRET_KEY"].strip())
today = R.today_uae().isoformat()
ev = db.get("events", {"select": "id,title,start_date,end_date,start_time,venue,city,status,price_text,source_name",
                       "status": "in.(approved,pending)", "or": f"(start_date.gte.{today},end_date.gte.{today})", "limit": "5000"})
print("EVENTS", len(ev))
STOP = {"the","a","an","in","at","of","and","live","dubai","abu","dhabi","uae","2026","2027","presents","by","with","ft","for","&","-","–"}
def toks(t): return {w for w in re.findall(r"[a-z0-9æ]+", t.lower()) if w not in STOP and len(w) > 1}
by = collections.defaultdict(list)
for e in ev: by[(e["start_date"], e["city"])].append(e)
for k, L in by.items():
    for a, b in itertools.combinations(L, 2):
        ta, tb = toks(a["title"]), toks(b["title"])
        if not ta or not tb: continue
        j = len(ta & tb) / len(ta | tb)
        if j >= 0.5 or (min(len(ta), len(tb)) >= 2 and (ta <= tb or tb <= ta)):
            print("DUP", a["start_date"], "|", a["id"], a["status"], a["start_time"], a["title"], "|", b["id"], b["status"], b["start_time"], b["title"])
for e in ev:
    t = e.get("start_time")
    if t:
        h, m = int(t[:2]), int(t[3:5])
        if m % 5 != 0 or 1 <= h <= 5:
            print("TIME", e["id"], e["status"], e["start_date"], t, "|", e["title"], "|", e.get("venue"))
    if e["status"] == "approved" and not e.get("venue"):
        print("NOVENUE", e["id"], e["start_date"], "|", e["title"], "|", e["city"])
de = db.get("deals", {"select": "id,title,venue,city,deal_type,price_text,status,days_of_week", "status": "in.(approved,pending)", "limit": "5000"})
print("DEALS", len(de))
byv = collections.defaultdict(list)
for d in de: byv[(R.norm(d.get("venue") or "")[:25], d["city"])].append(d)
for k, L in byv.items():
    for a, b in itertools.combinations(L, 2):
        ta, tb = toks(a["title"]), toks(b["title"])
        if ta and tb and (len(ta & tb) / len(ta | tb) >= 0.6) and a.get("days_of_week") == b.get("days_of_week"):
            print("DDUP", a["id"], a["status"], a["title"], "|", b["id"], b["status"], b["title"], "|", a.get("venue"))
for d in de:
    nums = [int(x.replace(",", "")) for x in re.findall(r"\b\d{1,3}(?:,\d{3})+\b|\b\d{3,6}\b", d.get("price_text") or "")]
    if nums and max(nums) >= 2000 and d.get("deal_type") not in ("staycation",):
        print("PRICE", d["id"], d["status"], d["deal_type"], "|", d["title"], "|", d.get("venue"), "|", d.get("price_text"))
