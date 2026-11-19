"""Test: chudszy tekst strony + tryb paczki (2 strony)."""
import os, json, glob, time
import anthropic
import run as R
client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"].strip())
srcs = []
for p in sorted(glob.glob("sources/*.json")):
    d = json.load(open(p))
    if isinstance(d, dict) and isinstance(d.get("sources"), list):
        srcs += d["sources"]
pick = [s for s in srcs if s["id"] in ("louvre_ad", "etihad_arena")] or srcs[:2]
pages = []
with R.Browser() as br:
    R._BROWSER = br
    for s in pick[:2]:
        pg = br.fetch(s["urls"][0])
        print("PAGE", s["id"], "full", len(pg.get("full_text") or ""), "lean", len(pg["text"]))
        pages.append((s, pg))
u_sync = {"input": 0, "output": 0, "calls": 0}
u_b = {"input": 0, "output": 0, "calls": 0}
R.BATCH["mode"] = "collect"
for s, pg in pages:
    try:
        R.call_model(client, pg["text"], R.clean_links(pg["links"], pg["final_url"]), s, pg["final_url"], None, u_b)
    except R.CollectOnly:
        pass
R.run_batch(client)
R.BATCH["mode"] = "use"
for s, pg in pages:
    out = R.call_model(client, pg["text"], R.clean_links(pg["links"], pg["final_url"]), s, pg["final_url"], None, u_b)
    print("RESULT", s["id"], "events", len(out.get("events", [])))
print("USAGE batch (po zniżce)", u_b)
