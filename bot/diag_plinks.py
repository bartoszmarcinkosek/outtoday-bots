import os, sys, re
sys.path.insert(0, os.path.dirname(__file__))
import run as R
T = {"73908edf-0f16-4404-b160-a4cf6e81465b":"thikra","89df640c-0473-4dbd-b785-7ad21660405f":"khalid abdul","d867826f-e96e-4c96-b79e-106761cf6797":"super cup",
 "33b0540c-0f6c-4e28-bad9-706c0805d597":"90","c5469b1e-d86b-418e-a69e-747d1c28450d":"elissa","074c8d22-5597-4421-a94d-238fabdf71d7":"diljit",
 "cd2c5d72-2502-4cf5-bbbc-3518a8812aea":"einaudi","29f02bdc-4510-49a8-893b-55547f694536":"kayan","31ca643c-c010-460a-ac0d-63d2c7be6903":"this-is-michael","8b1e3d4d-85f3-4f45-8a8a-616391d0cc9f":"rieu"}
seen = set()
with R.Browser() as br:
    for city in ("abu-dhabi", "dubai", "al-ain"):
        for p in range(1, 9):
            try:
                st, html = br.fetch_raw(f"https://{city}.platinumlist.net/event/list?page={p}")
            except Exception as e:
                print("L|err", city, p, e); continue
            for u in set(re.findall(r'https://[a-z-]+\.platinumlist\.net/event-tickets/\d+/[a-z0-9-]+', html)):
                if u in seen: continue
                seen.add(u)
                for k in ("thikra","khalid","abdulrahman","abdul-rahman","super-cup","90s","elissa","diljit","einaudi","kayan","michael","rieu"):
                    if k in u: print("L|", k, u)
print("L|total", len(seen))
