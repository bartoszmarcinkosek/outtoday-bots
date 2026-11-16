"""OutToday: codzienny e-mail do sprawdzenia wpisów.

Sekcje:
1. Gotowe do zatwierdzenia (bez braków)
2. Do uzupełnienia (brakuje godziny, ceny albo miejsca)
3. Zmiany wykryte przez bota w zatwierdzonych wpisach

Każdy przycisk prowadzi do strony outtoday-web/review.html z podpisanym tokenem.
Strona dopiero po kliknięciu "Potwierdź" zmienia coś w bazie.

Uruchomienie: python bot/digest.py            (wysyła e-mail, jeśli są MAIL_*)
              python bot/digest.py --preview  (tylko zapisuje out/digest.html)
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import hmac
import html
import json
import os
import smtplib
import sys
import time
from email.message import EmailMessage

import requests

UAE_TZ = dt.timezone(dt.timedelta(hours=4))
REVIEW_PAGE = os.environ.get("REVIEW_PAGE", "https://bartoszmarcinkosek.github.io/outtoday-web/review.html")
TOKEN_DAYS = 14
MAX_ROWS = 80

MONTHS_PL = ["sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"]
DAYS_PL = ["pon", "wt", "śr", "czw", "pt", "sob", "niedz"]
GAP_PL = {"start_time": "godzina", "price": "cena", "venue": "miejsce", "date": "data"}
FIELD_PL = {"price_text": "Cena", "start_time": "Godzina", "end_time": "Godzina końca", "venue": "Miejsce",
            "hours_text": "Godziny otwarcia", "days_of_week": "Dni", "official_url": "Oficjalna strona", "phone": "Telefon"}
TABLE_PL = {"events": "Event", "places": "Miejsce", "deals": "Promocja"}


# ---------------------------------------------------------------- tokeny (zgodne z supabase/functions/review/lib.ts)


def b64url(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def review_secret(key: str) -> str:
    return b64url(hmac.new(key.encode(), b"outtoday-review-v1", hashlib.sha256).digest())


def make_token(key: str, kind: str, row_id: str, days: int = TOKEN_DAYS, now: float | None = None) -> str:
    exp = int((now or time.time()) + days * 86400)
    body = b64url(json.dumps({"k": kind, "id": row_id, "exp": exp}, separators=(",", ":")).encode())
    sig = b64url(hmac.new(review_secret(key).encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def link(token: str, action: str) -> str:
    return f"{REVIEW_PAGE}?a={action}&t={token}"


# ---------------------------------------------------------------- dane


class DB:
    def __init__(self, url: str, key: str):
        self.base = url.rstrip("/") + "/rest/v1"
        self.h = {"apikey": key}
        if not key.startswith("sb_"):
            self.h["Authorization"] = f"Bearer {key}"

    def get(self, table: str, params: dict) -> list:
        r = requests.get(f"{self.base}/{table}", headers=self.h, params=params, timeout=30)
        r.raise_for_status()
        return r.json()


def load(db: DB) -> dict:
    today = dt.datetime.now(UAE_TZ).date().isoformat()
    cols = "id,title,start_date,end_date,start_time,venue,city,price_text,is_free,url,official_url,source_name,gaps,created_at"
    pending = db.get("events", {"select": cols, "status": "eq.pending", "order": "start_date.asc", "limit": "1000"})
    pending = [e for e in pending if (e.get("end_date") or e["start_date"]) >= today]
    changes = db.get("bot_changes", {"select": "*", "handled": "eq.false", "order": "created_at.asc", "limit": "500"})
    titles = {}
    sel = {"events": "id,title,start_date,official_url,url",
           "places": "id,name,official_url,url,city",
           "deals": "id,title,venue,official_url,url,city"}
    for table, cols in sel.items():
        ids = sorted({c["row_id"] for c in changes if c.get("table_name", "events") == table})
        for i in range(0, len(ids), 50):
            for e in db.get(table, {"select": cols, "id": f"in.({','.join(ids[i:i + 50])})"}):
                e["_table"] = table
                e.setdefault("title", e.get("name"))
                titles[e["id"]] = e
    sample, auto_changes = [], []
    if dt.datetime.now(UAE_TZ).weekday() == 0 or os.environ.get("FORCE_SAMPLE"):  # poniedziałek: kontrola bota
        week = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)).isoformat()
        auto = db.get("events", {"select": cols, "status": "eq.approved", "evidence->>auto": "eq.true",
                                 "verified_at": f"gte.{week}", "limit": "500"})
        import random
        sample = random.sample(auto, min(10, len(auto)))
        auto_changes = db.get("bot_changes", {"select": "*", "evidence": "like.[auto]*", "created_at": f"gte.{week}", "limit": "200"})
        for table in ("places", "deals"):
            ids = sorted({c["row_id"] for c in auto_changes if c["table_name"] == table and c["row_id"] not in titles})
            for i in range(0, len(ids), 50):
                for e in db.get(table, {"select": sel[table], "id": f"in.({','.join(ids[i:i + 50])})"}):
                    e["_table"] = table
                    e.setdefault("title", e.get("name"))
                    titles[e["id"]] = e
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=31)).isoformat()
    runs = db.get("bot_runs", {"select": "finished_at,summary", "dry_run": "eq.false", "finished_at": f"gte.{since}",
                               "order": "finished_at.asc", "limit": "500"})
    return {"pending": pending, "changes": changes, "events_by_id": titles, "sample": sample, "auto_changes": auto_changes,
            "runs": runs}


# Cennik Claude Haiku 5.5 (prompty do 100 tys. tokenów) i narzędzia web search, USD.
PRICE_IN, PRICE_OUT, PRICE_SEARCH = 0.10 / 1e6, 0.50 / 1e6, 10 / 1000


def run_cost(summary: dict) -> float:
    u = (summary or {}).get("usage") or {}
    return u.get("input", 0) * PRICE_IN + u.get("output", 0) * PRICE_OUT + u.get("searches", 0) * PRICE_SEARCH


def health(runs: list[dict]) -> tuple[str, list[str]]:
    """Koszt (wczoraj, 30 dni) i źródła, które dziś nic nie dały, choć zwykle dają."""
    now = dt.datetime.now(dt.timezone.utc)
    day = [r for r in runs if r["finished_at"] >= (now - dt.timedelta(hours=26)).isoformat()]
    c_day = sum(run_cost(r["summary"]) for r in day)
    c_month = sum(run_cost(r["summary"]) for r in runs)
    line = f"Koszt AI: ostatnia doba {c_day:.2f} USD, ostatnie 30 dni {c_month:.2f} USD (limit konta 25 USD/mies.)."
    # Źródła: ostatni przebieg z danym źródłem vs. wcześniejsze przebiegi.
    hist: dict[str, list[int]] = {}
    last: dict[str, dict] = {}
    for r in runs:
        per: dict[str, int] = {}
        status: dict[str, str] = {}
        skip: set[str] = set()
        for s in (r.get("summary") or {}).get("sources") or []:
            name = s.get("source")
            if not name:
                continue
            st = s.get("status") or ""
            if "bez zmian" in st:  # strona się nie zmieniła: AI nie czytało, 0 nic nie znaczy
                skip.add(name)
            per[name] = per.get(name, 0) + int(s.get("kept") or 0)
            status[name] = st
        for name, kept in per.items():
            if name in skip and kept == 0:
                continue
            hist.setdefault(name, []).append(kept)
            last[name] = {"status": status[name]}
    alarms = []
    for name, vals in hist.items():
        if len(vals) < 3:
            continue
        prev = sorted(vals[:-1])
        median = prev[len(prev) // 2]
        if vals[-1] == 0 and median >= 3:
            st = (last[name].get("status") or "")[:80]
            alarms.append(f"{name}: dziś 0 wydarzeń, zwykle ok. {median}. Stan strony: {st or 'brak danych'}.")
    return line, alarms


# ---------------------------------------------------------------- HTML

C = {"bg": "#f4f6fb", "card": "#ffffff", "text": "#14213d", "muted": "#5b6b88", "line": "#e3e8f2",
     "ok": "#1f9d55", "no": "#c0392b", "edit": "#2f6fde", "warn": "#b7791f"}


def plural(n: int, one: str, few: str, many: str) -> str:
    if n == 1:
        return one
    if n % 10 in (2, 3, 4) and n % 100 not in (12, 13, 14):
        return few
    return many


def fmt_date(e: dict) -> str:
    def one(s: str) -> str:
        d = dt.date.fromisoformat(s)
        return f"{DAYS_PL[d.weekday()]} {d.day} {MONTHS_PL[d.month - 1]}"
    out = one(e["start_date"])
    if e.get("end_date") and e["end_date"] != e["start_date"]:
        out += f" – {one(e['end_date'])}"
    if e.get("start_time"):
        out += f", {e['start_time'][:5]}"
    return out


def btn(href: str, label: str, color: str) -> str:
    return (f'<a href="{html.escape(href)}" style="display:inline-block;margin:2px 4px 2px 0;padding:7px 11px;'
            f'border-radius:6px;background:{color};color:#fff;text-decoration:none;font-size:13px;font-weight:600">{label}</a>')


def title_link(e: dict) -> str:
    href = e.get("official_url") or e.get("url")
    t = html.escape(e.get("title") or "?")
    if href:
        return f'<a href="{html.escape(href)}" style="color:{C["edit"]};font-weight:700;text-decoration:underline">{t}</a>'
    return f"<b>{t}</b>"


def event_row(e: dict, key: str) -> str:
    tok = make_token(key, "ev", e["id"])
    gaps = [GAP_PL.get(g, g) for g in (e.get("gaps") or [])]
    price = "Free" if e.get("is_free") else (e.get("price_text") or "")
    lines = [
        title_link(e),
        f'<span style="color:{C["text"]}">{html.escape(fmt_date(e))}</span>',
        html.escape(", ".join(x for x in [e.get("venue") or "", "" if (e.get("city") or "") in (e.get("venue") or "") else e.get("city") or ""] if x)) or f'<i style="color:{C["warn"]}">brak miejsca</i>',
    ]
    if price:
        lines.append(html.escape(price))
    if gaps:
        lines.append(f'<span style="color:{C["warn"]};font-weight:600">Brakuje: {html.escape(", ".join(gaps))}</span>')
    waiting = ""
    if e.get("created_at"):
        days = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(e["created_at"].replace("Z", "+00:00"))).days
        if days >= 1:
            waiting = f' · <b style="color:{C["warn"]}">czeka {days} {plural(days, "dzień", "dni", "dni")}</b>'
    lines.append(f'<span style="color:{C["muted"]};font-size:12px">Źródło: {html.escape(e.get("source_name") or "")}{waiting}</span>')
    buttons = btn(link(tok, "approve"), "✓ Zatwierdź", C["ok"]) + btn(link(tok, "reject"), "✕ Odrzuć", C["no"]) + btn(link(tok, "edit"), "✎ Uzupełnij", C["edit"])
    return (f'<tr><td style="padding:12px 14px;border-bottom:1px solid {C["line"]};font-size:14px;line-height:1.5">'
            + "<br>".join(lines) + f'<div style="margin-top:8px">{buttons}</div></td></tr>')


def change_row(c: dict, ev: dict | None, key: str) -> str:
    tok = make_token(key, "ch", c["id"])
    t = title_link(ev) if ev else "<b>(wpis usunięty)</b>"
    kind = TABLE_PL.get(c.get("table_name", "events"), "")
    if ev and ev.get("start_date"):
        when = html.escape(fmt_date(ev))
    else:
        when = html.escape(" · ".join(x for x in [kind, (ev or {}).get("venue") or "", (ev or {}).get("city") or ""] if x))
    field = FIELD_PL.get(c["field"], c["field"])
    src = f' · <a href="{html.escape(c["source_url"])}" style="color:{C["muted"]}">strona źródłowa</a>' if c.get("source_url") else ""
    if c["field"] == "official_url" and c.get("new_value"):
        src = f' · <a href="{html.escape(c["new_value"])}" style="color:{C["muted"]}">otwórz proponowaną stronę</a>'
    label = "Uzasadnienie" if c["field"] == "official_url" else "Cytat"
    ev_txt = f'<br><span style="color:{C["muted"]};font-size:12px">{label}: „{html.escape(c["evidence"])}”</span>' if c.get("evidence") else ""
    buttons = btn(link(tok, "accept"), "✓ Przyjmij zmianę", C["ok"]) + btn(link(tok, "ignore"), "Zostaw jak jest", C["muted"])
    return (f'<tr><td style="padding:12px 14px;border-bottom:1px solid {C["line"]};font-size:14px;line-height:1.5">'
            f'{t}<br>{when}<br><b>{field}:</b> {html.escape(c.get("old_value") or "–")} → <b>{html.escape(c.get("new_value") or "–")}</b>{src}{ev_txt}'
            f'<div style="margin-top:8px">{buttons}</div></td></tr>')


def sample_row(e: dict, key: str) -> str:
    tok = make_token(key, "ev", e["id"])
    price = "Free" if e.get("is_free") else (e.get("price_text") or "")
    lines = [title_link(e), html.escape(fmt_date(e)), html.escape(e.get("venue") or ""), html.escape(price),
             f'<span style="color:{C["muted"]};font-size:12px">Źródło: {html.escape(e.get("source_name") or "")}</span>']
    buttons = btn(link(tok, "reject"), "✕ Wycofaj z apki", C["no"]) + btn(link(tok, "edit"), "✎ Popraw", C["edit"])
    return (f'<tr><td style="padding:12px 14px;border-bottom:1px solid {C["line"]};font-size:14px;line-height:1.5">'
            + "<br>".join(x for x in lines if x) + f'<div style="margin-top:8px">{buttons}</div></td></tr>')


def auto_change_row(c: dict, ev: dict | None) -> str:
    name = html.escape((ev or {}).get("title") or "?")
    field = FIELD_PL.get(c["field"], c["field"])
    return (f'<tr><td style="padding:9px 14px;border-bottom:1px solid {C["line"]};font-size:13px;line-height:1.45">'
            f'<b>{name}</b> · {field}: {html.escape(c.get("new_value") or "")}'
            + (f' · <a href="{html.escape(c["source_url"])}" style="color:{C["muted"]}">źródło</a>' if c.get("source_url") else "")
            + "</td></tr>")


def section(title: str, note: str, rows: list[str], extra: int) -> str:
    if not rows:
        return ""
    more = f'<tr><td style="padding:10px 14px;color:{C["muted"]};font-size:13px">…i {extra} więcej (pojawią się w kolejnych e-mailach)</td></tr>' if extra > 0 else ""
    return (f'<h2 style="font-size:17px;color:{C["text"]};margin:26px 0 4px">{title}</h2>'
            f'<div style="color:{C["muted"]};font-size:13px;margin-bottom:8px">{note}</div>'
            f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:{C["card"]};border:1px solid {C["line"]};border-radius:10px;border-collapse:separate">'
            + "".join(rows) + more + "</table>")


def health_html(runs: list[dict]) -> str:
    line, alarms = health(runs)
    al = "".join(f'<li style="margin:4px 0">{a}</li>' for a in alarms)
    al_html = (f'<div style="color:{C["no"]};font-weight:600;margin-top:8px">Źródła do sprawdzenia:</div>'
               f'<ul style="margin:4px 0 0 18px;padding:0;color:{C["text"]};font-size:13px">{al}</ul>') if alarms else ""
    return (f'<h2 style="font-size:17px;color:{C["text"]};margin:26px 0 4px">Koszty i źródła</h2>'
            f'<div style="color:{C["muted"]};font-size:13px">{line}</div>{al_html}')


def build(data: dict, key: str) -> tuple[str, str, str, int]:
    ready = [e for e in data["pending"] if not e.get("gaps")]
    gaps = [e for e in data["pending"] if e.get("gaps")]
    changes = data["changes"]
    total = len(ready) + len(gaps) + len(changes) + len(data.get("sample", []))
    today = dt.datetime.now(UAE_TZ).date()

    budget = MAX_ROWS
    def take(items):
        nonlocal budget
        shown = items[:max(budget, 0)]
        budget -= len(shown)
        return shown, len(items) - len(shown)

    r_shown, r_more = take(ready)
    g_shown, g_more = take(gaps)
    c_shown, c_more = take(changes)

    body = (
        f'<div style="background:{C["bg"]};padding:18px 10px;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:{C["text"]}">'
        f'<div style="max-width:640px;margin:0 auto">'
        f'<h1 style="font-size:20px;margin:0 0 4px">OutToday · {today.day} {MONTHS_PL[today.month - 1]}</h1>'
        f'<div style="color:{C["muted"]};font-size:14px">{len(ready)} gotowe · {len(gaps)} do uzupełnienia · {len(changes)} {plural(len(changes), "zmiana", "zmiany", "zmian")}. '
        f'Tytuł otwiera stronę źródłową. Przyciski otwierają stronę z potwierdzeniem.</div>'
        + section("1. Gotowe do zatwierdzenia", "Wszystkie pola są potwierdzone cytatem ze strony.", [event_row(e, key) for e in r_shown], r_more)
        + section("2. Do uzupełnienia", "Strona nie podaje wszystkiego. Uzupełnij albo zatwierdź tak, jak jest.", [event_row(e, key) for e in g_shown], g_more)
        + section("3. Zmiany i propozycje", "Bot znalazł na stronie oficjalnej inną wartość niż w apce albo proponuje stronę oficjalną. Nic nie zostało zmienione.",
                  [change_row(c, data["events_by_id"].get(c["row_id"]), key) for c in c_shown], c_more)
        + section("4. Kontrola: losowe wpisy zatwierdzone przez bota", "Raz w tygodniu. Jeśli coś jest źle, wycofaj i daj znać, poprawimy bota.",
                  [sample_row(e, key) for e in data.get("sample", [])], 0)
        + section("5. Uzupełnione automatycznie w tym tygodniu", "Telefony i godziny z oficjalnych stron, potwierdzone cytatem.",
                  [auto_change_row(c, data["events_by_id"].get(c["row_id"])) for c in data.get("auto_changes", [])[:40]],
                  max(0, len(data.get("auto_changes", [])) - 40))
        + health_html(data.get("runs", []))
        + f'<p style="color:{C["muted"]};font-size:12px;margin-top:24px">Linki są ważne {TOKEN_DAYS} dni. '
          f'Nie przekazuj tego e-maila dalej: przyciski działają bez logowania.</p></div></div>'
    )
    subject = f"OutToday: {len(ready) + len(gaps)} do sprawdzenia" + (f", {len(changes)} {plural(len(changes), 'zmiana', 'zmiany', 'zmian')}" if changes else "") + f" · {today.day} {MONTHS_PL[today.month - 1]}"
    text = (f"OutToday {today.isoformat()}: {len(ready)} gotowe, {len(gaps)} do uzupełnienia, {len(changes)} zmian. "
            "Otwórz ten e-mail w widoku HTML, żeby zobaczyć przyciski.")
    return subject, body, text, total


def send(subject: str, html_body: str, text: str) -> None:
    user, pwd = os.environ["MAIL_USER"].strip(), os.environ["MAIL_PASSWORD"].replace(" ", "").strip()
    to = [a.strip() for a in os.environ["MAIL_TO"].split(",") if a.strip()]
    msg = EmailMessage()
    msg["Subject"], msg["From"], msg["To"] = subject, f"OutToday bot <{user}>", ", ".join(to)
    msg.set_content(text)
    msg.add_alternative(html_body, subtype="html")
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as s:
        s.login(user, pwd)
        s.send_message(msg)
    print(f"Wysłano e-mail do {len(to)} odbiorców.")


def selftest(db: DB, url: str, key: str) -> int:
    """Sprawdza funkcję review: zły token = 401, dobry token = odczyt wpisu (bez zmian w bazie)."""
    fn = url.rstrip("/") + "/functions/v1/review"
    origin = "https://bartoszmarcinkosek.github.io"
    r = requests.options(fn, headers={"Origin": origin, "Access-Control-Request-Method": "POST"}, timeout=30)
    print("CORS:", r.status_code, r.headers.get("access-control-allow-origin"))
    r = requests.post(fn, json={"token": "x.y", "action": "approve"}, headers={"Origin": origin}, timeout=30)
    print("zły token:", r.status_code, r.text[:80])
    ok = r.status_code == 401
    rows = db.get("events", {"select": "id,title,status", "status": "eq.pending", "limit": "1"})
    if rows:
        tok = make_token(key, "ev", rows[0]["id"])
        r = requests.post(fn, json={"token": tok, "action": "get"}, headers={"Origin": origin}, timeout=30)
        got = r.json().get("event", {}) if r.ok else {}
        print("dobry token:", r.status_code, "tytuł się zgadza" if got.get("title") == rows[0]["title"] else r.text[:120])
        ok = ok and r.status_code == 200 and got.get("title") == rows[0]["title"]
    print("SELFTEST", "OK" if ok else "BŁĄD")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", action="store_true", help="nie wysyłaj, zapisz out/digest.html")
    ap.add_argument("--selftest", action="store_true", help="sprawdź funkcję review, nic nie zmieniaj")
    ap.add_argument("--always", action="store_true", help="wyślij nawet, gdy nie ma nic do sprawdzenia")
    args = ap.parse_args()

    url, key = os.environ.get("SUPABASE_URL", "").strip(), os.environ.get("SUPABASE_SECRET_KEY", "").strip()
    if not url or not key:
        print("Brak SUPABASE_URL / SUPABASE_SECRET_KEY")
        return 1
    if args.selftest:
        return selftest(DB(url, key), url, key)
    data = load(DB(url, key))
    subject, body, text, total = build(data, key)
    os.makedirs("out", exist_ok=True)
    print(f"{subject} (pozycji: {total})")
    if args.preview:
        with open("out/digest.html", "w", encoding="utf-8") as f:
            f.write(body)
        print("Zapisano out/digest.html (podgląd, bez wysyłki)")
        return 0
    if total == 0 and not args.always:
        print("Nic do sprawdzenia, e-mail nie jest wysyłany.")
        return 0
    if not all(os.environ.get(k) for k in ("MAIL_USER", "MAIL_PASSWORD", "MAIL_TO")):
        print("Brak MAIL_USER / MAIL_PASSWORD / MAIL_TO: e-mail nie wysłany")
        return 1
    send(subject, body, text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
