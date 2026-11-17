"""OutToday: które hotele / lokale mają WŁASNY newsletter na oficjalnej stronie.

Dla każdej strony z sources/hotels.json i sources/venues.json (z poszanowaniem robots.txt):
- szuka pola e-mail w formularzu newslettera (słowa newsletter / subscribe / sign up / stay in touch / offers),
- sprawdza, czy formularz ma CAPTCHA (reCAPTCHA, hCaptcha, Turnstile),
- odróżnia stronę konkretnego hotelu od strony całej sieci (adres strony głównej sieci = sieć).
Nic nie wysyła. Wynik: tabela w logu + plik newsletters.json (artefakt).
Uruchomienie: python bot/newsletter_scan.py [--limit 400]
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(__file__))
import run as R  # noqa: E402

SRC = os.path.join(os.path.dirname(__file__), "..", "sources")

JS = r"""() => {
  const kw = /newsletter|subscribe|sign ?up|stay in touch|stay updated|join our (mailing|list)|exclusive offers|latest offers/i;
  const out = [];
  for (const inp of document.querySelectorAll('input')) {
    const t = (inp.type || '').toLowerCase();
    const hint = (inp.name + ' ' + inp.id + ' ' + inp.placeholder + ' ' + (inp.getAttribute('aria-label') || '')).toLowerCase();
    if (!(t === 'email' || hint.includes('mail'))) continue;
    let box = inp.closest('form') || inp.parentElement;
    for (let i = 0; i < 4 && box && box.innerText.length < 40; i++) box = box.parentElement;
    const ctx = (box ? box.innerText : '').slice(0, 400);
    const isLogin = !!(box && box.querySelector('input[type=password]'));
    if (isLogin || !kw.test(ctx + ' ' + hint)) continue;
    const scope = inp.closest('form') || document;
    const captcha = !!scope.querySelector('.g-recaptcha,[data-sitekey],iframe[src*="recaptcha"],iframe[src*="hcaptcha"],iframe[src*="turnstile"],[name="cf-turnstile-response"],[name="g-recaptcha-response"]')
                 || !!document.querySelector('script[src*="recaptcha/api.js"],script[src*="hcaptcha"],script[src*="turnstile"]');
    out.push({ctx: ctx.replace(/\s+/g, ' ').slice(0, 160), captcha});
  }
  const links = [...document.querySelectorAll('a[href]')].filter(a => /newsletter|subscribe/i.test(a.innerText + ' ' + a.href)).map(a => a.href).slice(0, 3);
  return {forms: out, links};
}"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=500)
    a = ap.parse_args()
    items = []
    for f, kind in (("hotels.json", "hotel"), ("venues.json", "venue")):
        for x in json.load(open(os.path.join(SRC, f), encoding="utf-8")):
            items.append({**x, "kind": x.get("kind") or kind})
    items = items[: a.limit]
    results = []
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        br = pw.chromium.launch()
        for it in items:
            url = it["url"]
            ok, why = R.robots_allows(url)
            if not ok:
                results.append({**it, "status": "robots"})
                continue
            path = [p for p in urlparse(url).path.split("/") if p]
            chain_home = len(path) <= 1 and it["kind"] == "hotel" and any(
                c in urlparse(url).netloc for c in ("marriott", "hilton", "ihg", "accor", "hyatt", "radisson", "wyndham", "rotana", "jumeirah.com", "kempinski"))
            ctx = br.new_context(user_agent=R.USER_AGENT, locale="en-US")
            page = ctx.new_page()
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=40_000)
                page.wait_for_timeout(3500)
                page.mouse.wheel(0, 20000)
                page.wait_for_timeout(1500)
                res = page.evaluate(JS)
                final = page.url
            except Exception as e:
                results.append({**it, "status": f"błąd {type(e).__name__}"})
                ctx.close()
                continue
            ctx.close()
            forms = res.get("forms") or []
            if forms:
                st = "CAPTCHA" if any(f["captcha"] for f in forms) else "formularz"
            elif res.get("links"):
                st = "link"
            else:
                st = "brak"
            results.append({**it, "status": st, "final_url": final, "chain_page": chain_home,
                            "links": res.get("links") or [], "ctx": forms[0]["ctx"] if forms else ""})
            print(f"{st:10} {it['city']:15} {it['name'][:50]}", flush=True)
    json.dump(results, open("newsletters.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    from collections import Counter
    print("\nPodsumowanie:", dict(Counter(r["status"] for r in results)))
    print("\n| Status | Emirat | Miejsce | Strona |\n|---|---|---|---|")
    for r in sorted(results, key=lambda r: (r["status"], r["city"])):
        if r["status"] in ("formularz", "CAPTCHA", "link"):
            u = r["links"][0] if r["status"] == "link" and r.get("links") else r.get("final_url") or r["url"]
            print(f"| {r['status']} | {r['city']} | {r['name']} | {u} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
