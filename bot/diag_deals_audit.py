"""Tylko odczyt: audyt ofert – ile ofert na to samo miejsce, duplikaty (to samo miejsce + nakładające się dni/godziny),
oferty bez godziny i bez ceny, zwykłe ceny posiłków."""
import os, sys, re, collections
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
rows = db.get("deals", {"select": "id,title,venue,city,deal_type,days_of_week,start_time,end_time,price_text,details,source_name,official_url,created_at",
                        "status": "eq.approved", "limit": "3000"})
print(f"DA|total {len(rows)}")
def vkey(v):
    v = (v or "").lower()
    v = re.sub(r"\b(the|at|by|restaurant|bar|lounge|hotel|resort|&|and|spa)\b", " ", v)
    return " ".join(re.findall(r"[a-z0-9]+", v))[:40]
byv = collections.defaultdict(list)
for r in rows:
    byv[(r["city"], vkey(r["venue"]).split(",")[0][:25])].append(r)
multi = sorted(((k, v) for k, v in byv.items() if len(v) >= 3), key=lambda kv: -len(kv[1]))
print(f"DA|venues_with_3plus {len(multi)} deals_in_them {sum(len(v) for k, v in multi)}")
for (c, v), lst in multi[:60]:
    print(f"DV|{c}|{v}|{len(lst)}|" + "; ".join(f"{x['deal_type']}:{(x['title'] or '')[:35]}" for x in lst))
# duplikaty: ten sam venue, ta sama godzina startu, wspólne dni
dups = 0
for k, lst in byv.items():
    for i, a in enumerate(lst):
        for b in lst[i + 1:]:
            da, dbb = set(a.get("days_of_week") or []), set(b.get("days_of_week") or [])
            same_t = (a.get("start_time") or "x") == (b.get("start_time") or "y")
            if same_t and (not da or not dbb or da & dbb):
                dups += 1
                print(f"DD|{k[0]}|{a['id']}|{a['deal_type']}|{(a['title'] or '')[:50]}|{b['id']}|{b['deal_type']}|{(b['title'] or '')[:50]}|{a.get('start_time')}|{(a.get('price_text') or '')[:40]}|{(b.get('price_text') or '')[:40]}")
print(f"DA|dup_pairs {dups}")
thin = [r for r in rows if not r.get("start_time") and not r.get("price_text")]
print(f"DA|no_time_no_price {len(thin)}")
for r in thin:
    print(f"DT|{r['city']}|{r['id']}|{r['deal_type']}|{(r['title'] or '')[:60]}|{(r['venue'] or '')[:50]}|{(r.get('details') or '')[:90]}")
plain = [r for r in rows if r["deal_type"] in ("breakfast", "business_lunch", "dinner") and not re.search(r"(free|off|%|unlimited|free.?flow|kids eat|1\s*\+\s*1|two for|2 for|half|deal|offer|special|inclusive|all.you)", ((r.get("price_text") or "") + " " + (r.get("details") or "") + " " + (r.get("title") or "")).lower())]
print(f"DA|plain_meal_prices {len(plain)}")
for r in plain:
    print(f"DP|{r['city']}|{r['id']}|{r['deal_type']}|{(r['title'] or '')[:50]}|{(r['venue'] or '')[:45]}|{(r.get('price_text') or '')[:50]}|{(r.get('details') or '')[:80]}")
