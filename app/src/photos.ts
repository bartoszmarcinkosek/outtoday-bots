// Zdjęcia kategorii na kartach (wygenerowane w Canvie, nasze). Zasady:
// 0) konkretne miejsce (Burj Khalifa, Louvre, Miracle Garden...) ma pierwszeństwo,
// 1) rodzaj eventu po słowach w tytule (rower → rower, bieg → bieganie...), 2) inaczej kategoria,
// 3) zdjęcia z widokiem konkretnego miasta tylko dla tego miasta, 4) ten sam wpis = zawsze to samo zdjęcie,
// 5) sąsiednie karty dostają różne wersje, gdy jest z czego wybierać.
import { Item } from './logic';
import { PHOTO_FILES } from './photos.gen';

// Konkretne miejsca (najważniejsze): event/miejsce/oferta w tym miejscu dostaje zdjęcie tego miejsca (klucz lm_*).
// Sprawdzane w tytule i w miejscu. Działa dopiero, gdy jest plik assets/photos/lm_<nazwa>-<n>.jpg.
const LANDMARKS: [RegExp, string][] = [
  [/burj khalifa|at the top\b|dubai fountain/i, 'lm_burj_khalifa'],
  [/louvre/i, 'lm_louvre'],
  [/miracle garden/i, 'lm_miracle_garden'],
  [/grand mosque|sheikh zayed mosque/i, 'lm_grand_mosque'],
  [/etihad arena/i, 'lm_etihad_arena'],
  [/coca[- ]?cola arena/i, 'lm_coca_cola_arena'],
  [/dubai opera/i, 'lm_dubai_opera'],
  [/madinat jumeirah|souk madinat/i, 'lm_madinat'],
  [/expo city|al wasl dome|al wasl plaza/i, 'lm_expo_city'],
  [/palm jumeirah|\bthe palm\b|atlantis/i, 'lm_palm'],
  [/saadiyat/i, 'lm_saadiyat'],
  [/reem island|\bal reem\b|reem mall|shams abu dhabi|gate towers|reem central park/i, 'lm_reem'],
  [/corniche/i, 'lm_corniche'],
  [/museum of the future/i, 'lm_museum_future'],
  [/global village/i, 'lm_global_village'],
  [/yas marina circuit/i, 'lm_yas_marina_circuit'],
  [/qasr al watan/i, 'lm_qasr_al_watan'],
  [/dubai frame/i, 'lm_dubai_frame'],
  [/burj al arab/i, 'lm_burj_al_arab'],
  [/ain dubai/i, 'lm_ain_dubai'],
  [/jebel jais/i, 'lm_jebel_jais'],
];

const RULES: [RegExp, string][] = [
  [/aviation|skydiv|parachut|paraglid|paramotor|gyrocopter|balloon flight|hot air balloon|seaplane|helicopter|microlight|zip ?line|xline|bungee|\bifly\b|jais flight|aerobatic|flying (lesson|experience)|scenic flight/i, 'flying'],
  [/\bski\b|ski dubai|snow abu dhabi|snow park|ice rink|ice skating|on ice\b/i, 'snow'],
  [/board ?gam|boardgam|game night|\bchess\b|mahjong|scrabble|clocktower|polyglot|language exchange|language & culture|conversation (club|meetup|café|cafe)|conversations over coffee/i, 'community'],
  [/\bdance\b|dancing|salsa|bachata|kizomba|tango|heels|twerk|afrobeats dance|hip ?hop class|zumba|belly ?dance|riverdance/i, 'dance'],
  [/kayak|paddle ?board|\bsup\b|jet ?ski|wakeboard|kite ?surf|\bsurf|scuba|diving|deep dive|snorkel|flyboard|sail ?gp|sail grand prix|regatta|sailing|rowing|aquafit/i, 'watersports'],
  [/\bcandlelight\b|orchestra|symphon|philharmon|quartet|classical|opera\b|recital|piano|violin/i, 'candlelight'],
  [/comedy|stand[- ]?up|comedian/i, 'comedy'],
  [/theat(re|er)|musical\b|ballet|\bplay\b|pantomime|swan lake|nutcracker/i, 'theatre'],
  [/cinema|film|screening|movie/i, 'cinema'],
  [/\bjazz\b/i, 'jazz'],
  [/\bdj\b|techno|afro ?house|\bedm\b|rave|club night/i, 'dj'],
  [/arabic music|tarab|\boud\b|khaleeji|eid concert/i, 'arabic'],
  [/\brock\b|\bmetal\b|\bpunk\b/i, 'rock'],
  [/horse|equestrian|racecourse|endurance ride|show jumping|polo\b/i, 'horse'],
  [/cycl|\bbike ride|\bbicycle|velo\b/i, 'cycling'],
  [/swim|triathlon|aquathlon|open water/i, 'swimming'],
  [/\brun\b|running|marathon|\b(3|5|10|21)k\b|\d+ ?km\b|parkrun|race run|trail race|relay/i, 'running'],
  [/yoga|pilates|fitness|bootcamp|hiit|workout/i, 'yoga'],
  [/cricket|\bt10\b|\bt20\b|ilt20|knight riders|dubai capitals|desert vipers|gulf giants|mi emirates|sharjah warriorz/i, 'cricket'],
  [/football|soccer|super cup|\bfc\b|pro league|manchester city/i, 'football'],
  [/tennis|padel|squash|pickleball/i, 'padel'],
  [/golf/i, 'golf'],
  [/grand prix|formula|\bf1\b|motor|karting|kartdrome|autodrome|rally|drift|baja|desert challenge|nitro circus|car show|car and bike|bike week|driving experience/i, 'motorsport'],
  [/\bcamels?\b/i, 'camel'],
  [/karaoke/i, 'night_out'],
  [/\bquiz\b/i, 'quiz'],
  [/\bbooks?\b|book (club|fair|launch|presentation)|library|reading|poetry/i, 'books'],
  [/\btalk\b|lecture|panel|in conversation|seminar/i, 'talk'],
  [/night market|flea|bazaar|farmers'? market|winter market|christmas market|craft market|food market|urban market|souq|souk/i, 'market'],
  // na końcu: bieg w parku archeologicznym to nadal bieg
  [/heritage village|heritage area|old village|pearling village|abandoned village|\bfort\b|castle|archaeolog|ruins|mud ?brick|historic (district|site|neighbourhood)|al fahidi|al bastakiya|heart of sharjah|qasr al hosn|\bhisn\b/i, 'heritage'],
];

// kategoria (events/places/deals) → klucz zdjęć; sport bez rodzaju → pula różnych sportów
const CAT: Record<string, string[]> = {
  music: ['music'], culture: ['culture'], sport: [], food: ['food'],
  festivals: ['festivals'], festival: ['festivals'], nightlife: ['nightlife'], classes: ['classes'], nature: ['nature'],
  community: ['community'], business: ['talk'], family: ['family'], market: ['market'],
  beaches: ['beaches'], parks: ['parks'], museums: ['museums'], attractions: ['attractions'], active: ['active'],
  kids: ['kids'], markets: ['souk'], studios: ['studios'], daytrips: ['daytrips'],
  day_pass: ['day_pass'], ladies_night: ['ladies_night'], brunch: ['brunch'], happy_hour: ['happy_hour'], night_out: ['night_out'], lunch: ['lunch'],
  dinner: ['dinner'], quiz: ['quiz'], breakfast: ['breakfast'], staycation: ['staycation'],
};

// Zdjęcia z widokiem miasta: klucz_miasto (np. day_pass_dubai) – dodawane do puli tylko w tym mieście.
const CITY_SUFFIX: Record<string, string> = { Dubai: 'dubai', 'Abu Dhabi': 'abudhabi', Sharjah: 'sharjah', 'Ras Al Khaimah': 'rak' };

// Gdy wpis pasuje do tych rodzajów, a zdjęcia jeszcze nie ma: lepiej ikonka niż obce zdjęcie z kategorii.
const NO_FALLBACK = new Set(['flying', 'watersports', 'heritage', 'dance', 'snow']);

function hash(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) h = Math.imul(h ^ s.charCodeAt(i), 16777619);
  return h >>> 0;
}

function pool(item: Item): number[] {
  let keys: string[] | undefined;
  const placeText = `${item.title} ${item.where ?? ''} ${item.event?.venue ?? ''}`;
  const lm = LANDMARKS.find(([re]) => re.test(placeText));
  if (lm && PHOTO_FILES[lm[1]]) return [...PHOTO_FILES[lm[1]]];
  if (item.kind !== 'deal' || !item.catKey || item.catKey === 'other') {
    const hit = RULES.find(([re]) => re.test(item.title));
    if (hit && PHOTO_FILES[hit[1]]) keys = [hit[1]];
    else if (hit && NO_FALLBACK.has(hit[1])) return [];
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
