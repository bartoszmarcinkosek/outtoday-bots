// Diagnostyka: do jakich rejonów trafiają zatwierdzone pozycje (ta sama logika co apka).
import { placeOf } from '../src/zones';
const URL = process.env.SUPABASE_URL!.trim();
const KEY = 'sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS';
async function get(t: string) {
  const r = await fetch(`${URL}/rest/v1/${t}?select=*`, { headers: { apikey: KEY } });
  return (await r.json()) as any[];
}
(async () => {
  const counts: Record<string, number> = {};
  const none: string[] = [];
  for (const e of await get('events')) {
    const f = placeOf(e.city, e.venue, e.area);
    const p = f.zone ? f : placeOf(e.city, e.source_name);
    const k = `${p.city} / ${p.zone}`; counts[k] = (counts[k] ?? 0) + 1;
    if (!p.zone && p.city === 'Dubai') none.push(`E ${e.venue} | ${e.area}`);
  }
  for (const x of await get('places')) {
    const p = placeOf(x.city, x.name, x.area);
    const k = `${p.city} / ${p.zone}`; counts[k] = (counts[k] ?? 0) + 1;
    if (!p.zone && p.city === 'Dubai') none.push(`P ${x.name} | ${x.area}`);
  }
  for (const [k, v] of Object.entries(counts).sort()) console.log('ZONE', k, v);
  const freq: Record<string, number> = {};
  for (const n of none) freq[n] = (freq[n] ?? 0) + 1;
  for (const [k, v] of Object.entries(freq).sort((a, b) => b[1] - a[1]).slice(0, 80)) console.log('NOZONE', v, k);
})();
