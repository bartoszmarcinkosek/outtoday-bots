"""Zrzuty ekranu aplikacji (wersja web) do App Store i Google Play."""
import sys, time
from playwright.sync_api import sync_playwright

URL = sys.argv[1]
SETS = {"ios-6.9": (440, 956, 3), "android": (360, 720, 3)}
GEO = {"latitude": 25.0805, "longitude": 55.1403}  # Dubai Marina

def shot(page, path):
    page.wait_for_timeout(2500)
    page.screenshot(path=path)
    print("saved", path)

def click_text(page, t):
    try:
        page.get_by_text(t, exact=True).last.click(timeout=5000)
        return True
    except Exception as e:
        print("no click", t, e.__class__.__name__)
        return False

with sync_playwright() as p:
    b = p.chromium.launch()
    for name, (w, h, dpr) in SETS.items():
        ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=dpr, is_mobile=True, has_touch=True,
                            geolocation=GEO, permissions=["geolocation"], locale="en-US", timezone_id="Asia/Dubai")
        page = ctx.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(8000)
        shot(page, f"out/{name}-1-today.png")
        click_text(page, "Events"); shot(page, f"out/{name}-2-events.png")
        try:
            page.locator("text=/AED|Free|FREE/").first.click(timeout=5000)
            shot(page, f"out/{name}-3-detail.png")
            page.keyboard.press("Escape"); page.wait_for_timeout(800)
            page.goto(URL, wait_until="networkidle"); page.wait_for_timeout(6000)
        except Exception as e:
            print("detail failed", e.__class__.__name__)
        click_text(page, "Deals"); shot(page, f"out/{name}-4-deals.png")
        click_text(page, "Places"); shot(page, f"out/{name}-5-places.png")
        click_text(page, "Top 10 in Dubai"); page.wait_for_timeout(800); shot(page, f"out/{name}-7-top10.png")
        click_text(page, "All places")
        click_text(page, "Filters"); shot(page, f"out/{name}-6-filters.png")
        ctx.close()
    b.close()
