// OutToday: obsługa przycisków z codziennego e-maila (Zatwierdź / Odrzuć / Uzupełnij / Przyjmij zmianę).
// Każdy link w e-mailu ma podpisany token (HMAC). Bez ważnego podpisu nic się nie zmienia.
// Funkcja zwraca tylko JSON; stronę z przyciskami serwuje GitHub Pages (outtoday-web).

const SUPABASE_URL = Deno.env.get("SUPABASE_URL") ?? "";
const KEY = Deno.env.get("OT_SECRET_KEY") ?? "";

type Token = { k: "ev" | "ch"; id: string; exp: number };

const enc = new TextEncoder();

function b64url(bytes: Uint8Array): string {
  let s = "";
  for (const b of bytes) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromB64url(s: string): Uint8Array {
  const pad = s.replace(/-/g, "+").replace(/_/g, "/") + "===".slice((s.length + 3) % 4);
  return Uint8Array.from(atob(pad), (c) => c.charCodeAt(0));
}

async function hmac(key: string, data: string): Promise<Uint8Array> {
  const k = await crypto.subtle.importKey("raw", enc.encode(key), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return new Uint8Array(await crypto.subtle.sign("HMAC", k, enc.encode(data)));
}

// Klucz do podpisów jest wyprowadzony z klucza Supabase, więc nie trzeba osobnego sekretu.
async function reviewSecret(): Promise<string> {
  return b64url(await hmac(KEY, "outtoday-review-v1"));
}

export async function verifyToken(token: string, now = Date.now()): Promise<Token | null> {
  const [body, sig] = (token || "").split(".");
  if (!body || !sig) return null;
  const expected = b64url(await hmac(await reviewSecret(), body));
  if (expected.length !== sig.length) return null;
  let diff = 0;
  for (let i = 0; i < sig.length; i++) diff |= expected.charCodeAt(i) ^ sig.charCodeAt(i);
  if (diff !== 0) return null;
  try {
    const t = JSON.parse(new TextDecoder().decode(fromB64url(body))) as Token;
    if (!t.id || (t.k !== "ev" && t.k !== "ch") || !t.exp || t.exp * 1000 < now) return null;
    if (!/^[0-9a-f-]{36}$/i.test(t.id)) return null;
    return t;
  } catch {
    return null;
  }
}

async function db(path: string, init: RequestInit = {}): Promise<any> {
  const r = await fetch(`${SUPABASE_URL}/rest/v1/${path}`, {
    ...init,
    headers: { apikey: KEY, "Content-Type": "application/json", Prefer: "return=representation", ...(init.headers ?? {}) },
  });
  const text = await r.text();
  if (!r.ok) throw new Error(`db ${r.status}: ${text.slice(0, 200)}`);
  return text ? JSON.parse(text) : null;
}

const EVENT_COLS =
  "id,title,category,start_date,end_date,start_time,end_time,venue,city,price_text,price_min_aed,is_free,url,official_url,source_name,source_url,status,evidence,gaps,description";

// Pola, które bot może zaproponować do zmiany, osobno dla każdej tabeli.
const CHANGE_FIELDS: Record<string, string[]> = {
  events: ["price_text", "start_time", "venue"],
  places: ["price_text", "hours_text", "official_url", "phone"],
  deals: ["price_text", "days_of_week", "start_time", "end_time", "official_url", "phone"],
};
const ROW_COLS: Record<string, string> = {
  events: EVENT_COLS,
  places: "id,name,category,area,city,hours_text,price_text,is_free,official_url,url,phone,status",
  deals: "id,title,venue,area,city,details,days_of_week,start_time,end_time,price_text,official_url,url,phone,status",
};

// Pola, które można poprawić z formularza "Uzupełnij", z prostą kontrolą formatu.
const EDITABLE: Record<string, (v: unknown) => unknown> = {
  title: (v) => str(v, 200, true),
  start_date: (v) => date(v, true),
  end_date: (v) => date(v, false),
  start_time: (v) => time(v),
  end_time: (v) => time(v),
  venue: (v) => str(v, 200, false),
  price_text: (v) => str(v, 200, false),
  price_min_aed: (v) => num(v),
  is_free: (v) => v === true || v === "true",
  official_url: (v) => url(v),
  description: (v) => str(v, 500, false),
};

class Bad extends Error {}

function str(v: unknown, max: number, required: boolean): string | null {
  const s = typeof v === "string" ? v.trim() : "";
  if (!s) {
    if (required) throw new Bad("pole wymagane");
    return null;
  }
  return s.slice(0, max);
}
function date(v: unknown, required: boolean): string | null {
  const s = str(v, 10, required);
  if (s && !/^\d{4}-\d{2}-\d{2}$/.test(s)) throw new Bad(`zła data: ${s}`);
  return s;
}
function time(v: unknown): string | null {
  const s = str(v, 5, false);
  if (s && !/^([01]\d|2[0-3]):[0-5]\d$/.test(s)) throw new Bad(`zła godzina: ${s}`);
  return s;
}
function num(v: unknown): number | null {
  if (v === null || v === undefined || v === "") return null;
  const n = Number(v);
  if (!Number.isFinite(n) || n < 0 || n > 100000) throw new Bad(`zła cena: ${v}`);
  return n;
}
function url(v: unknown): string | null {
  const s = str(v, 500, false);
  if (s && !/^https?:\/\//.test(s)) throw new Bad(`zły link: ${s}`);
  return s;
}

function priceNumber(text: string | null): number | null {
  const m = (text ?? "").replace(/,/g, "").match(/\d+(?:\.\d+)?/);
  return m ? Number(m[0]) : null;
}

export async function handle(body: any): Promise<{ status: number; data: unknown }> {
  const t = await verifyToken(body?.token);
  if (!t) return { status: 401, data: { error: "Link wygasł albo jest nieprawidłowy." } };
  const action = String(body?.action ?? "get");
  const now = new Date().toISOString();

  if (t.k === "ev") {
    const rows = await db(`events?id=eq.${t.id}&select=${EVENT_COLS}`);
    const ev = rows?.[0];
    if (!ev) return { status: 404, data: { error: "Nie ma już tego wpisu." } };
    if (action === "get") return { status: 200, data: { kind: "event", event: ev } };
    if (action === "approve" || action === "reject") {
      const status = action === "approve" ? "approved" : "rejected";
      const upd: Record<string, unknown> = { status, updated_at: now };
      if (status === "approved") upd.verified_at = now;
      const out = await db(`events?id=eq.${t.id}`, { method: "PATCH", body: JSON.stringify(upd) });
      return { status: 200, data: { ok: true, event: out?.[0] } };
    }
    if (action === "save") {
      const fields = body?.fields ?? {};
      const upd: Record<string, unknown> = { updated_at: now };
      try {
        for (const [k, fn] of Object.entries(EDITABLE)) if (k in fields) upd[k] = fn(fields[k]);
      } catch (e) {
        if (e instanceof Bad) return { status: 400, data: { error: e.message } };
        throw e;
      }
      if (upd.is_free === true) {
        upd.price_min_aed = 0;
        if (!upd.price_text) upd.price_text = "Free";
      }
      // braki aktualizujemy według tego, co teraz jest wypełnione
      const merged = { ...ev, ...upd };
      upd.gaps = [
        ...(merged.start_time ? [] : ["start_time"]),
        ...(merged.venue ? [] : ["venue"]),
        ...(merged.price_text || merged.is_free ? [] : ["price"]),
      ];
      if (body?.approve === true) {
        upd.status = "approved";
        upd.verified_at = now;
      }
      const out = await db(`events?id=eq.${t.id}`, { method: "PATCH", body: JSON.stringify(upd) });
      return { status: 200, data: { ok: true, event: out?.[0] } };
    }
    return { status: 400, data: { error: "Nieznana akcja." } };
  }

  // zmiana wykryta przez bota (events, places albo deals)
  const chs = await db(`bot_changes?id=eq.${t.id}&select=*`);
  const ch = chs?.[0];
  if (!ch) return { status: 404, data: { error: "Nie ma już tej zmiany." } };
  const table = ch.table_name as string;
  if (!(table in CHANGE_FIELDS)) return { status: 400, data: { error: "Nieznana tabela." } };
  const rows = await db(`${table}?id=eq.${ch.row_id}&select=${ROW_COLS[table]}`);
  const row = rows?.[0] ?? null;
  if (action === "get") return { status: 200, data: { kind: "change", change: ch, table, event: row } };
  if (action === "accept" || action === "ignore") {
    if (ch.handled) return { status: 200, data: { ok: true, already: true } };
    if (action === "accept") {
      if (!CHANGE_FIELDS[table].includes(ch.field)) return { status: 400, data: { error: "Tego pola nie można zmienić automatycznie." } };
      const upd: Record<string, unknown> = { updated_at: now };
      const v = ch.new_value === "" ? null : ch.new_value;
      if (ch.field === "days_of_week") {
        const names = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
        upd.days_of_week = v ? String(v).split(",").map((d) => names.indexOf(d.trim())).filter((i) => i >= 0) : null;
      } else {
        upd[ch.field] = v;
      }
      if (table === "events" && ch.field === "price_text") {
        const n = priceNumber(v);
        if (n !== null) upd.price_min_aed = n;
      }
      await db(`${table}?id=eq.${ch.row_id}`, { method: "PATCH", body: JSON.stringify(upd) });
    }
    await db(`bot_changes?id=eq.${ch.id}`, { method: "PATCH", body: JSON.stringify({ handled: true }) });
    return { status: 200, data: { ok: true } };
  }
  return { status: 400, data: { error: "Nieznana akcja." } };
}

