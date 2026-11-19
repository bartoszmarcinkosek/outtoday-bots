import re, requests, datetime as dt
cfg = open("app/src/config.ts").read()
url = re.search(r"SUPABASE_URL = '([^']+)'", cfg).group(1) + "/rest/v1"
key = re.search(r"SUPABASE_KEY = '([^']+)'", cfg).group(1)
h = {"apikey": key, "Authorization": f"Bearer {key}"}
cols = {'EventRow': ['id', 'title', 'description', 'category', 'start_date', 'end_date', 'start_time', 'end_time', 'venue', 'area', 'city', 'price_text', 'is_free', 'kid_friendly', 'price_min_aed', 'pet_friendly', 'ladies_only', 'official_url', 'lat', 'lng', 'phone', 'created_at', 'updated_at', 'registration_required', 'url', 'source_name', 'source_url', 'verified_at'], 'PlaceRow': ['id', 'name', 'description', 'category', 'area', 'city', 'hours_text', 'hours', 'price_text', 'is_free', 'kid_friendly', 'is_indoor', 'pet_friendly', 'ladies_only', 'official_url', 'lat', 'lng', 'phone', 'created_at', 'updated_at', 'url', 'source_name'], 'DealRow': ['id', 'deal_type', 'title', 'details', 'venue', 'area', 'city', 'days_of_week', 'start_time', 'end_time', 'price_text', 'valid_until', 'kid_friendly', 'pet_friendly', 'ladies_only', 'official_url', 'lat', 'lng', 'phone', 'created_at', 'updated_at', 'url', 'source_name']}
today = (dt.datetime.utcnow() + dt.timedelta(hours=4)).date().isoformat()
for t, tb in (("EventRow", "events"), ("PlaceRow", "places"), ("DealRow", "deals")):
    sel = ",".join(cols[t])
    p = {"select": sel, "limit": "2000"}
    if tb == "events":
        p["or"] = f"(end_date.gte.{today},and(end_date.is.null,start_date.gte.{today}))"
    r = requests.get(f"{url}/{tb}", headers=h, params=p, timeout=60)
    full = requests.get(f"{url}/{tb}", headers=h, params={"select": "*", "limit": "2000"}, timeout=60)
    print("ROW", tb, r.status_code, r.text[:200] if r.status_code != 200 else f"{len(r.json())} rows {len(r.content)//1024} KB vs select=* {len(full.json())} rows {len(full.content)//1024} KB")
