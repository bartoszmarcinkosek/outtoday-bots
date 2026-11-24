import os, sys, requests
u=os.environ["SUPABASE_URL"].strip(); k=os.environ["SUPABASE_SECRET_KEY"].strip()
for t in ("events","deals"):
    r=requests.get(f"{u}/rest/v1/{t}",params={"select":"*","limit":"1","order":"created_at.desc"},headers={"apikey":k,"Authorization":f"Bearer {k}"},timeout=30)
    print("Q|",t,r.status_code, list(r.json()[0].keys()) if r.ok and r.json() else r.text[:300])
