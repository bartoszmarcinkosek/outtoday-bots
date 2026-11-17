"""Renderuje stronę w przeglądarce i wypisuje tekst (bez AI). URL w zmiennej PAGE."""
import os, sys
from playwright.sync_api import sync_playwright
url = os.environ.get("PAGE", "https://www.yasmarinacircuit.com/en/trainyas")
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(user_agent="Mozilla/5.0 (OutToday bot; contact outtodayapp.uae@gmail.com)")
    pg.goto(url, wait_until="domcontentloaded", timeout=90000)
    pg.wait_for_timeout(12000)
    for label in ["TRAINAM", "TRAINYAS"]:
        pass
    txt = pg.inner_text("body")
    i = txt.upper().find("SCHEDULE")
    print("TXT|" + txt[max(0, i - 200): i + 4000].replace("\n", " ¶ "))
    b.close()
