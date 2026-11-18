// Zdjęcia kategorii na kartach (wygenerowane w Canvie, nasze). Zasady:
// 1) rodzaj eventu po słowach w tytule (rower → rower, bieg → bieganie...), 2) inaczej kategoria,
// 3) zdjęcia z widokiem konkretnego miasta tylko dla tego miasta, 4) ten sam wpis = zawsze to samo zdjęcie,
// 5) sąsiednie karty dostają różne wersje, gdy jest z czego wybierać.
import { Item } from './logic';
import { PHOTO_FILES } from './photos.gen';

const RULES: [RegExp, string][] = [
  [/\bcandlelight\b|orchestra|symphon|philharmon|quartet|classical|opera\b|recital|piano|violin/i, 'candlelight'],
  [/comedy|stand[- ]?up|comedian/i, 'comedy'],
  [/theat(re|er)|musical\b|ballet|\bplay\b|pantomime/i, 'theatre'],
  [/cinema|film|screening|movie/i, 'cinema'],
  [/\bjazz\b/i, 'jazz'],
  [/\bdj\b|techno|afro ?house|\bedm\b|rave|club night/i, 'dj'],
  [/arabic|tarab|\boud\b|khaleeji|eid concert/i, 'arabic'],
  [/\brock\b|\bmetal\b|\bpunk\b/i, 'rock'],
  [/cycl|\bbike\b|\bride\b|velo/i, 'cycling'],
  [/swim|triathlon|aquathlon|open water/i, 'swimming'],
  [/\brun\b|running|marathon|\b(5|10|21)k\b|parkrun|race run|trail race/i, 'running'],
  [/yoga|pilates|fitness|bootcamp|hiit|workout|zumba/i, 'yoga'],
  [/football|soccer|super cup|\bfc\b|pro league/i, 'football'],
  [/cricket|\bt10\b|\bt20\b|ilt20/i, 'cricket'],
  [/tennis|padel|squash|pickleball/i, 'padel'],
  [/\bgolf/i, 'golf'],
  [/grand prix|formula|\bf1\b|motor|karting|rally|drift|baja/i, 'motorsport'],
  [/camel/i, 'camel'],
  [/horse|equestrian|racecourse|endurance ride|show jumping/i, 'horse'],
  [/karaoke/i, 'night_out'],
  [/\bquiz\b/i, 'quiz'],
  [/\bbook|library|reading|poetry/i, 'books'],
  [/\btalk\b|lecture|panel|in conversation|seminar/i, 'talk'],
  [/market|bazaar|souq|souk|night market/i, 'market'],
];

// kategoria (events/places/deals) → klucz zdjęć; sport bez rodzaju → pula różnych sportów
const CAT: Record<string, string[]> = {
  music: ['music'], culture: ['culture'], sport: ['running', 'cycling', 'football', 'padel', 'yoga'], food: ['food'],
  festivals: ['festivals'], festival: ['festivals'], nightlife: ['nightlife'], classes: ['classes'], nature: ['nature'],
  community: ['community'], business: ['talk'], family: ['family'], market: ['market'],
  beaches: ['beaches'], parks: ['parks'], museums: ['museums'], attractions: ['attractions'], active: ['active'],
  kids: ['kids'], markets: ['souk'], studios: ['studios'], daytrips: ['daytrips'],
  day_pass: ['day_pass'], brunch: ['brunch'], happy_hour: ['happy_hour'], night_out: ['night_out'], lunch: ['lunch'],
  dinner: ['dinner'], quiz: ['quiz'], breakfast: ['breakfast'], staycation: ['staycation'],
};

// Zdjęcia z widokiem miasta: klucz_miasto (np. day_pass_dubai) – dodawane do puli tylko w tym mieście.
const CITY_SUFFIX: Record<string, string> = { Dubai: 'dubai', 'Abu Dhabi': 'abudhabi', Sharjah: 'sharjah', 'Ras Al Khaimah': 'rak' };

function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

function pool(item: Item): number[] {
  let keys: string[] | undefined;
  if (item.kind === 'event') {
    const hit = RULES.find(([re]) => re.test(item.title));
    if (hit && PHOTO_FILES[hit[1]]) keys = [hit[1]];
  }
  if (!keys) keys = CAT[item.catKey] ?? [];
  const suf = CITY_SUFFIX[item.city];
  const out: number[] = [];
  for (const k of keys) {
    out.push(...(PHOTO_FILES[k] ?? []));
    if (suf) out.push(...(PHOTO_FILES[`${k}_${suf}`] ?? []));
  }
  return out;
}

/** Zdjęcie dla karty albo null (wtedy karta pokazuje ikonkę). `avoid` = zdjęcie poprzedniej karty. */
export function photoFor(item: Item, avoid?: number | null): number | null {
  const p = pool(item);
  if (!p.length) return null;
  let i = hash(item.key) % p.length;
  if (p.length > 1 && p[i] === avoid) i = (i + 1) % p.length;
  return p[i];
}
