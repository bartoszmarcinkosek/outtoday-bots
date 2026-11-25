// Kontrola zdjęć (darmowa, tylko odczyt): dla każdej karty wypisuje, jakie zdjęcie dostaje w apce.
// Linie: PA|rodzaj|id|miasto|kategoria|zdjęcie|tytuł|miejsce   oraz   PC|zdjęcie|ile kart   (zdjęcie "-" = ikonka)
import { buildItems } from '../src/logic';
import { photoFor } from '../src/photos';
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

(async () => {
  const today = new Date(Date.now() + 4 * 3600 * 1000).toISOString().slice(0, 10);
  const data: any = process.env.SAMPLE ? JSON.parse(process.env.SAMPLE) : {
    events: (await all('events', '*')).filter((e) => (e.end_date ?? e.start_date) >= today),
    places: await all('places', '*'),
    deals: await all('deals', '*'),
  };
  const items = buildItems(data, null);
  const count: Record<string, number> = {};
  const clean = (s: unknown) => String(s ?? '').replace(/[|\n]/g, ' ').slice(0, 70);
  for (const i of items) {
    const p = photoFor(i) as unknown as string | null;
    const name = p ? p.replace(/^.*\//, '').replace(/\.jpg$/, '') : '-';
    count[name] = (count[name] ?? 0) + 1;
    const row: any = i.event ?? i.deal ?? i.place ?? {};
    console.log(`PA|${i.kind}|${row.id}|${clean(row.city)}|${clean(i.catKey)}|${name}|${clean((i as any).rawTitle ?? i.title)}|${clean(i.where)}`);
  }
  for (const [k, n] of Object.entries(count).sort((a, b) => b[1] - a[1])) console.log(`PC|${k}|${n}`);
})().catch((e) => { console.error(e); process.exit(1); });
