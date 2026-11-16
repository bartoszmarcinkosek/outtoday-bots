import os, requests
URL = os.environ["SUPABASE_URL"].strip(); KEY = os.environ["SUPABASE_SECRET_KEY"].strip()
rows = requests.get(f"{URL}/rest/v1/places?select=name,city,status&limit=5000", headers={"apikey": KEY}, timeout=30).json()
for c in ("Al Ain", "Ras Al Khaimah", "Sharjah", "Ajman", "Fujairah", "Umm Al Quwain"):
    print("NAMES", c, "|", "; ".join(sorted(r["name"] for r in rows if r["city"] == c)))
print("NAMES AD-alain |", "; ".join(sorted(r["name"] for r in rows if r["city"] == "Abu Dhabi" and "ain" in r["name"].lower())))
