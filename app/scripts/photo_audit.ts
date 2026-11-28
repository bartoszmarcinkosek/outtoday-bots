// Kontrola zdjęć (darmowa, tylko odczyt): dla każdej karty wypisuje, jakie zdjęcie dostaje w apce.
// Linie: PA|rodzaj|id|miasto|kategoria|zdjęcie|tytuł|miejsce   oraz   PC|zdjęcie|ile kart   (zdjęcie "-" = ikonka)
import { buildItems } from '../src/logic';
import { photoFor } from '../src/photos';
import { PHOTO_NAMES } from '../src/photos.gen';
import { SUPABASE_KEY, SUPABASE_URL } from '../src/config';

async function all(table: string, select: string, extra = ''): Promise<any[]> {
  const out: any[] = [];
  for (let from = 0; ; from += 1000) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/${table}?select=${select}&status=eq.approved&order=id${extra}`, {
      headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}`, Range: `${from}-${from + 999}` },
    });
    if (!res.ok) throw new Error(`${table}: ${res.status} ${await res.text()}`);
    const page = await res.json();
    out.push(...page);
    if (page.length < 1000) return out;
  }
}

// zdjęcia z Unsplash mają numery (900001+), zdjęcia z paczki – ścieżki plików
const nameOf = (p: unknown): string => (p == null ? '-' : typeof p === 'number' ? `${PHOTO_NAMES.get(p) ?? p}` : String(p).replace(/^.*\//, '').replace(/\.jpg$/, ''));

(async () => {
  const today = new Date(Date.now() + 4 * 3600 * 1000).toISOString().slice(0, 10);
  const data: any = process.env.SAMPLE ? JSON.parse(process.env.SAMPLE) : {
    events: (await all('events', '*')).filter((e) => (e.end_date ?? e.start_date) >= today),
    places: await all('places', '*'),
    deals: await all('deals', '*'),
  };
  const items = buildItems(data, null);
  const days = Number(process.env.DAYS || 0);   // DAYS=2 → linie PA tylko dla pozycji dodanych w ostatnich 2 dniach (PC zawsze z całej bazy)
  const since = days ? new Date(Date.now() - days * 86400000).toISOString() : '';
  const count: Record<string, number> = {};
  const clean = (s: unknown) => String(s ?? '').replace(/[|\n]/g, ' ').slice(0, 70);
  for (const i of items) {
    const p = photoFor(i) as unknown as string | null;
    const name = nameOf(p);
    count[name] = (count[name] ?? 0) + 1;
    const row: any = i.event ?? i.deal ?? i.place ?? {};
    if (!since || String(row.created_at ?? '') >= since) console.log(`PA|${i.kind}|${row.id}|${clean(row.city)}|${clean(i.catKey)}|${name}|${clean((i as any).rawTitle ?? i.title)}|${clean(i.where)}`);
  }
  for (const [k, n] of Object.entries(count).sort((a, b) => b[1] - a[1])) console.log(`PC|${k}|${n}`);
  // Tester: wybór kart do obejrzenia (PT|...) – pomija id obejrzane w ostatnich 7 dniach (audit/tester_seen.json).
  // Kolejność: (a) dodane w ostatnich 2 dniach, (b) eventy startujące w ciągu 7 dni, (c) reszta – najdawniej oglądane/nigdy najpierw.
  try {
    const fs = require('fs');
    const seen: Record<string, string> = JSON.parse(fs.readFileSync('../audit/tester_seen.json', 'utf8'));
    const cut = new Date(Date.now() - 7 * 86400000 + 4 * 3600 * 1000).toISOString().slice(0, 10);
    const new2 = new Date(Date.now() - 2 * 86400000).toISOString();
    const in7 = new Date(Date.now() + 7 * 86400000 + 4 * 3600 * 1000).toISOString().slice(0, 10);
    const rows = items.map((i) => ({ i, row: (i.event ?? i.deal ?? i.place ?? {}) as any }))
      .filter(({ row }) => row.id && !((seen[row.id] ?? '') >= cut));
    const tier = ({ i, row }: any) => (String(row.created_at ?? '') >= new2 ? 0 : i.kind === 'event' && row.start_date <= in7 ? 1 : 2);
    rows.sort((a, b) => tier(a) - tier(b) || (seen[a.row.id] ?? '').localeCompare(seen[b.row.id] ?? '') || String(a.row.id).localeCompare(String(b.row.id)));
    const total = items.length;
    const covered = items.filter((i) => ((seen[((i.event ?? i.deal ?? i.place ?? {}) as any).id] ?? '') >= cut)).length;
    console.log(`PS|cards ${total}|seen7d ${covered}|todo ${rows.length}`);
    for (const { i, row } of rows.slice(0, Number(process.env.PICK || 140))) {
      const p = photoFor(i) as unknown as string | null;
      const name = nameOf(p);
      const d = [row.start_date, row.end_date].filter(Boolean).join('..');
      const price = row.is_free ? 'FREE' : clean(row.price_text ?? row.price_min_aed ?? '');
      console.log(`PT|${tier({ i, row })}|${i.kind}|${row.id}|${clean(row.city)}|${clean(i.catKey)}|${clean(row.deal_type ?? row.category ?? '')}|${name}|${clean((i as any).rawTitle ?? i.title)}|${clean(i.where)}|${d}|${price}|${clean(row.official_url).slice(0, 60)}|${String(row.description ?? row.details ?? '').replace(/[|\n]/g, ' ').slice(0, 140)}`);
    }
  } catch (e) { console.log(`PS|error ${e}`); }
})().catch((e) => { console.error(e); process.exit(1); });
