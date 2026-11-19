import requests
K = "sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS"
r = requests.get("https://ibpuispeimyyqiailjfy.supabase.co/rest/v1/events?id=eq.3060573e-e8a2-4359-9af6-20a41db1cb39&status=eq.approved&select=title,category,start_date,end_date,start_time,end_time,venue,area,city,price_text,is_free,description,official_url,url&limit=1",
                 headers={"apikey": K, "Authorization": "Bearer " + K, "Origin": "https://outtodayapp.github.io"})
print("T |", r.status_code, r.headers.get("access-control-allow-origin"), r.text[:300])
