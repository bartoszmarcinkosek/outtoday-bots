"""Tylko odczyt: szczegóły podejrzanych duplikatów (lista id w IDS)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import run as R
db = R.DB(os.environ["SUPABASE_URL"].strip(), os.environ["SUPABASE_SECRET_KEY"].strip())
IDS = """110f47e7-f672-482b-9006-d746954abd60 b0d36b0f-caea-4844-9918-799de8671592 2f07583d-082c-4fa0-9163-47a85c91420d
95bb8b55-5ac7-4aa4-92d0-aadf4434120f c80c871b-050e-47ac-97fb-af9a943d76df 3b5a9945-22ab-4a4f-83bf-67051a148420
97240443-f0a0-460c-b9ee-d048090655fb ca4d9add-d4a7-4a7a-8360-b535186b84a2 4c4547e3-d6b1-4391-9ac2-6e932f42e248
8936ae37-de06-4d80-adec-15835cbc1261 66d2b571-2bae-497d-a7fd-b83997d19441 8e8d9c87-a7b4-4106-ab29-d60b44807e08
a6547eb3-af24-4690-8f14-f510e183700b d34480bc-d0c0-421d-b8e1-40884fae8faf 31f29cb0-c35a-4f6e-aa3b-29976d83cd62
6d32917f-240a-4ecb-b3af-a0f1044b2f63 493b2fe8-8603-463c-b867-ff4ef002dc3e""".split()
rows = db.get("events", {"select": "id,title,venue,city,start_date,end_date,start_time,end_time,price_text,is_free,source_name,official_url,url,description",
                         "id": f"in.({','.join(IDS)})"})
for r in rows:
    r["description"] = (r.get("description") or "")[:120]
    print("X|" + json.dumps(r, ensure_ascii=False))
