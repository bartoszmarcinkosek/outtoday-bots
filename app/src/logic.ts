import type { Ionicons } from '@expo/vector-icons';
import type { ComponentProps } from 'react';
import type { AppData, DealRow, EventRow, PlaceRow } from './api';
import { NEW_BASELINE } from './config';
import { fmtCardWhen, fmtDate, fmtDays, fmtTime, fmtWhen, isLongRunning } from './dates';
import { CategoryStyle, cat, dealStyle } from './theme';
import { ZONE_CENTER, distanceKm, placeOf } from './zones';
import { topRank } from './top10';

export type IconName = ComponentProps<typeof Ionicons>['name'];
export type Kind = 'event' | 'place' | 'deal';

// Jedna wspólna postać dla wydarzeń, miejsc i promocji. Dzięki niej karty,
// wyszukiwarka, ulubione i sortowanie działają tak samo we wszystkich zakładkach.
export type Item = {
  key: string; // np. "event:1234"
  kind: Kind;
  title: string;
  rawTitle?: string; // tytuł bez nazwy miejsca (do doboru zdjęć)
  catKey: string;
  look: CategoryStyle;
  icon: IconName;
  when: string | null; // linia na karcie
  whenFull: string | null; // w szczegółach
  where: string | null;
  mapQuery: string;
  description: string | null;
  priceText: string | null;
  price: number | null; // w AED, 0 = za darmo, null = nie podano
  free: boolean;
  kid: boolean;
  pet: boolean;
  ladies: boolean;
  indoor: boolean | null; // tylko miejsca
  top: number | null; // miejsce w Top 10 miasta (tylko miejsca)
  zone: string | null;
  city: string;
  km: number | null;
  geo: [number, number] | null; // dokładne współrzędne miejsca, gdy znane
  officialUrl: string | null;
  phone: string | null;
  sourceName: string | null;
  checked: string | null; // "Nov 2026"
  verified: boolean; // potwierdzone na stronie organizatora
  isNew: boolean;
  created: string | null; // created_at z bazy
  endsSoon: boolean;
  booking: boolean;
  event?: EventRow;
  place?: PlaceRow;
  deal?: DealRow;
};

const ICONS: Record<string, IconName> = {
  music: 'musical-notes', culture: 'color-palette', sport: 'fitness', food: 'restaurant',
  festivals: 'sparkles', festival: 'sparkles', market: 'bag-handle', nightlife: 'moon',
  classes: 'school', nature: 'leaf', community: 'people', business: 'briefcase', family: 'happy',
  beaches: 'water', parks: 'leaf', museums: 'business', attractions: 'star', active: 'bicycle',
  kids: 'happy', markets: 'bag-handle', studios: 'brush', daytrips: 'car',
  day_pass: 'sunny', ladies_night: 'wine', brunch: 'cafe', happy_hour: 'beer', night_out: 'mic',
  quiz: 'help-circle', lunch: 'briefcase', dinner: 'restaurant', breakfast: 'cafe-outline', staycation: 'bed',
};

const VENUE_STOP = new Set(['the','hotel','resort','and','spa','beach','club','by','at','al','abu','dhabi','dubai','ain','sharjah','ras','khaimah','restaurant','bar','lounge']);
/** Deals often have generic titles ("Day Pass", "Brunch") - put the venue first. */
export function withVenue(title: string, venue?: string | null): string {
  const v = (venue ?? '').split(',')[0].trim();
  if (!v || v.length > 45) return title;
  const t = title.toLowerCase();
  const words = v.toLowerCase().split(/[^a-z0-9\u00c0-\u024f]+/).filter((w) => w.length >= 3 && !VENUE_STOP.has(w));
  if (!words.length || words.some((w) => t.includes(w))) return title;
  return `${v} · ${title}`;
}

export function iconFor(key: string | null | undefined): IconName {
  return ICONS[key ?? ''] ?? 'pricetag';
}

export function todayIso(now: Date = new Date()): string {
  const m = String(now.getMonth() + 1).padStart(2, '0');
  const d = String(now.getDate()).padStart(2, '0');
  return `${now.getFullYear()}-${m}-${d}`;
}

function addDaysIso(days: number, now: Date = new Date()): string {
  const x = new Date(now.getFullYear(), now.getMonth(), now.getDate() + days);
  return todayIso(x);
}

export function placeLine(venue: string | null, area: string | null): string | null {
  if (!venue) return area;
  if (!area) return venue;
  if (venue.toLowerCase().includes(area.toLowerCase())) return venue;
  return `${venue} · ${area}`;
}

// Pierwsza kwota w tekście ceny. "Free" daje 0, brak kwoty daje null.
export function parsePrice(text: string | null | undefined): number | null {
  if (!text) return null;
  const m = text.match(/AED\s*([\d,]+(?:\.\d+)?)/i);
  // "Free" tylko gdy darmowe dla wszystkich: "Free for ladies…", "Free before 9pm", "Free with…" + kwota AED to NIE jest darmowe.
  if (/^\s*free\b/i.test(text) && !m && !/^\s*free\s+(for|with|before|until|till|on|if|to|after|when)\b/i.test(text)) return 0;
  if (!m) return null;
  const n = Number(m[1].replace(/,/g, ''));
  return Number.isFinite(n) ? n : null;
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

function monthYear(ts: string | null | undefined): string | null {
  if (!ts) return null;
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return null;
  return `${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}

function isNew(created: string | null | undefined, now: Date): boolean {
  if (!created) return false;
  const day = created.slice(0, 10);
  return day >= NEW_BASELINE && day >= addDaysIso(-7, now);
}

function geoOf(r: { lat?: number | null; lng?: number | null }): [number, number] | null {
  return r.lat != null && r.lng != null ? [r.lat, r.lng] : null;
}

// Odległość: do dokładnego miejsca, gdy znamy współrzędne; inaczej do środka dzielnicy.
function kmFor(zone: string | null, me: [number, number] | null, geo: [number, number] | null = null): number | null {
  if (!me) return null;
  if (geo) return distanceKm(me, geo);
  if (!zone || !ZONE_CENTER[zone]) return null;
  return distanceKm(me, ZONE_CENTER[zone]);
}

export function dealTimes(d: DealRow): string {
  const s = fmtTime(d.start_time);
  const e = fmtTime(d.end_time);
  if (s && e) return `${s} to ${e}`;
  if (s) return `from ${s}`;
  return '';
}

// Gdy w bazie nie ma informacji "w środku / na zewnątrz", zgadujemy po kategorii.
const OUT_CATS = ['beaches', 'parks', 'daytrips'];
const IN_CATS = ['museums', 'markets', 'studios'];

export function buildItems(data: AppData, me: [number, number] | null, now: Date = new Date()): Item[] {
  const soon = addDaysIso(7, now);
  const today = todayIso(now);
  const out: Item[] = [];

  for (const e of data.events) {
    const first = placeOf(e.city, e.venue, e.area);
    // Gdy z miejsca nie da się ustalić dzielnicy (np. "WH 3"), próbujemy po nazwie źródła ("Alserkal Avenue").
    const { city: itemCity, zone } = first.zone ? first : placeOf(e.city, e.source_name);
    const price = e.is_free ? 0 : e.price_min_aed ?? parsePrice(e.price_text);
    const end = e.end_date ?? e.start_date;
    if (eventOverToday(e, now)) continue;
    out.push({
      key: `event:${e.id}`, kind: 'event', title: e.title, catKey: e.category, look: cat(e.category),
      icon: iconFor(e.category), when: fmtCardWhen(e, now), whenFull: fmtWhen(e),
      where: placeLine(e.venue, e.area), mapQuery: `${e.venue ?? e.area ?? e.title}, ${e.city}`,
      description: e.description, priceText: e.price_text, price, free: e.is_free || price === 0,
      kid: e.kid_friendly === true, pet: e.pet_friendly === true, ladies: e.ladies_only === true,
      indoor: null, top: null, zone, city: itemCity, km: kmFor(zone, me, geoOf(e)), geo: geoOf(e),
      officialUrl: e.official_url ?? null, phone: e.phone ?? null, sourceName: e.source_name,
      checked: monthYear(e.verified_at ?? e.updated_at ?? e.created_at), verified: !!e.verified_at, isNew: isNew(e.created_at, now), created: e.created_at ?? null,
      endsSoon: isLongRunning(e) && end >= today && end <= soon, booking: e.registration_required, event: e,
    });
  }

  for (const p of data.places) {
    const { city: itemCity, zone } = placeOf(p.city, p.name, p.area);
    const price = p.is_free ? 0 : parsePrice(p.price_text);
    out.push({
      key: `place:${p.id}`, kind: 'place', title: p.name, catKey: p.category, look: cat(p.category),
      icon: iconFor(p.category), when: p.hours_text, whenFull: p.hours_text, where: p.area,
      mapQuery: `${p.name}, ${p.city}`, description: p.description, priceText: p.price_text, price,
      free: p.is_free || price === 0, kid: p.kid_friendly === true, pet: p.pet_friendly === true,
      ladies: p.ladies_only === true, indoor: p.is_indoor ?? (OUT_CATS.includes(p.category ?? '') ? false : IN_CATS.includes(p.category ?? '') ? true : null), top: topRank(itemCity, p.name), zone, city: itemCity,
      km: kmFor(zone, me, geoOf(p)), geo: geoOf(p), officialUrl: p.official_url ?? null, phone: p.phone ?? null,
      sourceName: p.source_name, checked: monthYear(p.updated_at ?? p.created_at), verified: false,
      isNew: isNew(p.created_at, now), created: p.created_at ?? null, endsSoon: false, booking: false, place: p,
    });
  }

  for (const d of data.deals) {
    const { city: itemCity, zone } = placeOf(d.city, d.venue, d.area);
    const price = parsePrice(d.price_text);
    const times = dealTimes(d);
    const daysTxt = d.deal_type === 'staycation' && !(d.days_of_week ?? []).length
      ? (d.valid_until ? `Book by ${fmtDate(d.valid_until)}` : 'Hotel stay offer') : fmtDays(d.days_of_week);
    const when = `${daysTxt}${times ? ` · ${times}` : ''}`;
    out.push({
      key: `deal:${d.id}`, kind: 'deal', title: withVenue(d.title, d.venue), rawTitle: d.title, catKey: d.deal_type ?? '', look: dealStyle(d.deal_type),
      icon: iconFor(d.deal_type), when, whenFull: when, where: placeLine(d.venue, d.area),
      mapQuery: `${d.venue ?? d.title}, ${d.city}`, description: d.details, priceText: d.price_text, price,
      free: price === 0, kid: d.kid_friendly === true, pet: d.pet_friendly === true,
      ladies: d.ladies_only === true || d.deal_type === 'ladies_night', indoor: null, top: null, zone,
      city: itemCity, km: kmFor(zone, me, geoOf(d)), geo: geoOf(d), officialUrl: d.official_url ?? null,
      phone: d.phone ?? null, sourceName: d.source_name, checked: monthYear(d.updated_at ?? d.created_at), verified: false,
      isNew: isNew(d.created_at, now), created: d.created_at ?? null,
      endsSoon: !!d.valid_until && d.valid_until >= today && d.valid_until <= soon, booking: false, deal: d,
    });
  }
  return out;
}

export function dealOnDay(d: DealRow, dow: number): boolean {
  return (d.days_of_week ?? []).includes(dow);
}

// Promocja trwa w tej chwili: dziś jest jej dzień i mieścimy się w godzinach.
export function dealOnNow(d: DealRow, now: Date = new Date()): boolean {
  if (!dealOnDay(d, now.getDay()) || !d.start_time) return false;
  const hm = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const end = d.end_time ? d.end_time.slice(0, 5) : '23:59';
  return d.start_time.slice(0, 5) <= hm && hm <= end;
}

// Promocja była dziś, ale jej godziny już minęły (np. lunch 12–15, a jest 16:00).
export function dealEndedToday(d: DealRow, now: Date = new Date()): boolean {
  if (!dealOnDay(d, now.getDay()) || !d.end_time) return false;
  const hm = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const end = d.end_time.slice(0, 5);
  const start = d.start_time ? d.start_time.slice(0, 5) : '00:00';
  return end > start && hm > end; // end <= start = po północy (np. 22:00–02:00), wtedy nie uznajemy za zakończoną
}

// Event, który kończy się dziś i jego godzina już minęła (np. 09:30–11:00, a jest 18:00) – nie pokazujemy.
// Bez godziny końca: jednodniowy event znika 3 godziny po starcie.
export function eventOverToday(e: EventRow, now: Date = new Date()): boolean {
  const end = e.end_date ?? e.start_date;
  if (end !== todayIso(now)) return false;
  const mins = now.getHours() * 60 + now.getMinutes();
  const toMin = (t: string) => Number(t.slice(0, 2)) * 60 + Number(t.slice(3, 5));
  if (e.end_time) {
    const et = toMin(e.end_time);
    const st = e.start_time ? toMin(e.start_time) : 0;
    return et > st && mins > et; // koniec po północy (np. 22:00–02:00) – nie chowamy
  }
  if (e.start_time && !e.end_date) return mins > toMin(e.start_time) + 180;
  return false;
}

// Czy miejsce jest teraz otwarte (z tabeli godzin). null = nie wiemy.
export function placeOpen(p: PlaceRow | undefined, now: Date = new Date()): { open: boolean; until?: string } | null {
  const h = p?.hours;
  if (!h || !Object.keys(h).length) return null;
  const hm = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
  const d = now.getDay();
  for (const [a, b] of h[String(d)] ?? []) {
    if (b > a ? hm >= a && hm < b : hm >= a) return { open: true, until: b === '24:00' && a === '00:00' ? undefined : b === '24:00' ? 'midnight' : b };
  }
  // zmiana zaczęta wczoraj i trwająca po północy, np. 18:00–02:00
  for (const [a, b] of h[String((d + 6) % 7)] ?? []) {
    if (b <= a && b !== '24:00' && hm < b) return { open: true, until: b };
  }
  return { open: false };
}

export type SortKey = 'default' | 'near' | 'price';
export const SORT_LABEL: Record<SortKey, string> = { default: 'Recommended', near: 'Nearest', price: 'Price' };

const big = Number.MAX_SAFE_INTEGER;
const byKm = (a: Item, b: Item) => (a.km ?? big) - (b.km ?? big);
const byPrice = (a: Item, b: Item) => (a.price ?? big) - (b.price ?? big);

export function sortItems(items: Item[], sort: SortKey, now: Date = new Date()): Item[] {
  const today = todayIso(now);
  const dow = now.getDay();
  const eff = (i: Item) => (i.event && i.event.start_date > today ? i.event.start_date : today);
  const base = (a: Item, b: Item): number => {
    if (a.kind === 'event' && b.kind === 'event') {
      return eff(a).localeCompare(eff(b)) || byKm(a, b) || a.title.localeCompare(b.title);
    }
    if (a.kind === 'deal' && b.kind === 'deal') {
      const ta = Number(dealOnDay(b.deal!, dow)) - Number(dealOnDay(a.deal!, dow));
      return ta || byKm(a, b) || a.title.localeCompare(b.title);
    }
    return byKm(a, b) || a.title.localeCompare(b.title);
  };
  const copy = [...items];
  if (sort === 'near') return copy.sort((a, b) => byKm(a, b) || base(a, b));
  if (sort === 'price') return copy.sort((a, b) => byPrice(a, b) || base(a, b));
  copy.sort(base);
  return mixEvents(copy, today);
}

// "Recommended" dla eventów: w obrębie tego samego dnia najpierw wydarzenia krótkie
// (koncert, spektakl), potem długie (wystawy trwające ponad tydzień), a kategorie
// na przemian, żeby jedna galeria z 30 wystawami nie zasłaniała reszty.
function mixEvents(sorted: Item[], today: string): Item[] {
  const out: Item[] = [];
  const eff = (i: Item) => (i.event && i.event.start_date > today ? i.event.start_date : today);
  const long = (i: Item) => {
    const e = i.event;
    if (!e || !e.end_date) return false;
    return (Date.parse(e.end_date) - Date.parse(e.start_date)) / 86400000 > 7;
  };
  let k = 0;
  while (k < sorted.length) {
    const it = sorted[k];
    if (it.kind !== 'event') { out.push(it); k++; continue; }
    const day = eff(it);
    let j = k;
    while (j < sorted.length && sorted[j].kind === 'event' && eff(sorted[j]) === day) j++;
    const group = sorted.slice(k, j);
    for (const part of [group.filter((i) => !long(i)), group.filter(long)]) {
      const byCat = new Map<string, Item[]>();
      for (const i of part) {
        const c = i.event?.category ?? '';
        if (!byCat.has(c)) byCat.set(c, []);
        byCat.get(c)!.push(i);
      }
      const queues = [...byCat.values()];
      while (queues.some((q) => q.length)) for (const q of queues) if (q.length) out.push(q.shift()!);
    }
    k = j;
  }
  return out;
}

// Słowa, po których wyszukiwarka przenosi od razu do gotowej zakładki z filtrem.
export type Shortcut = { tab: 'events' | 'places' | 'deals'; key: string; label: string };
const SHORTCUTS: [string[], Shortcut][] = [
  [['brunch'], { tab: 'deals', key: 'brunch', label: 'Brunch deals' }],
  [['day pass', 'daypass', 'pool pass', 'daycation'], { tab: 'deals', key: 'day_pass', label: 'Day passes' }],
  [['staycation', 'hotel stay', 'weekend stay'], { tab: 'deals', key: 'staycation', label: 'Staycations' }],
  [['happy hour'], { tab: 'deals', key: 'happy_hour', label: 'Happy hours' }],
  [['ladies night', "ladies' night", 'ladies'], { tab: 'deals', key: 'ladies_night', label: "Ladies' nights" }],
  [['quiz'], { tab: 'deals', key: 'quiz', label: 'Quiz nights' }],
  [['business lunch', 'lunch'], { tab: 'deals', key: 'lunch', label: 'Business lunches' }],
  [['karaoke', 'comedy', 'night out'], { tab: 'deals', key: 'night_out', label: 'Nights out' }],
  [['dinner'], { tab: 'deals', key: 'dinner', label: 'Dinner deals' }],
  [['beach', 'beaches', 'pool'], { tab: 'places', key: 'beaches', label: 'Beaches & Pools' }],
  [['park', 'parks'], { tab: 'places', key: 'parks', label: 'Parks & Nature' }],
  [['museum', 'museums', 'gallery'], { tab: 'places', key: 'museums', label: 'Museums & Culture' }],
  [['kids', 'play area', 'playground'], { tab: 'places', key: 'kids', label: 'Kids & Play' }],
  [['mall', 'malls', 'souk', 'souks', 'market'], { tab: 'places', key: 'markets', label: 'Markets & Malls' }],
  [['day trip', 'day trips'], { tab: 'places', key: 'daytrips', label: 'Day Trips' }],
  [['farm', 'farms', 'oasis', 'oases', 'desert'], { tab: 'places', key: 'daytrips', label: 'Day Trips (farms, oases, desert)' }],
  [['pottery', 'studio', 'classes'], { tab: 'places', key: 'studios', label: 'Classes & Studios' }],
  [['padel', 'cycling', 'running', 'kayak'], { tab: 'places', key: 'active', label: 'Sport & Active' }],
  [['concert', 'concerts', 'music', 'show', 'shows'], { tab: 'events', key: 'music', label: 'Music & Shows' }],
  [['festival', 'festivals'], { tab: 'events', key: 'festivals', label: 'Festivals' }],
  [['exhibition', 'art', 'culture'], { tab: 'events', key: 'culture', label: 'Culture & Art' }],
  [['sport', 'sports', 'fitness', 'race', 'run'], { tab: 'events', key: 'sport', label: 'Sport & Fitness' }],
  [['workshop', 'workshops'], { tab: 'events', key: 'classes', label: 'Classes & Workshops' }],
];

export function shortcutsFor(query: string): Shortcut[] {
  const q = query.trim().toLowerCase();
  if (q.length < 3) return [];
  return SHORTCUTS.filter(([words]) => words.some((w) => w === q || w.startsWith(q))).map(([, s]) => s);
}

// Odległość edycyjna z limitem (literówki): przerywa, gdy różnica przekracza max.
function editDist(a: string, b: string, max: number): number {
  if (Math.abs(a.length - b.length) > max) return max + 1;
  let prev2: number[] = [];
  let prev = Array.from({ length: b.length + 1 }, (_, j) => j);
  for (let i = 1; i <= a.length; i++) {
    const cur = [i];
    let best = i;
    for (let j = 1; j <= b.length; j++) {
      cur[j] = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
      // zamienione sąsiednie litery ("nigth" → "night") liczą się jako jeden błąd
      if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) cur[j] = Math.min(cur[j], prev2[j - 2] + 1);
      if (cur[j] < best) best = cur[j];
    }
    if (best > max) return max + 1;
    prev2 = prev;
    prev = cur;
  }
  return prev[b.length];
}

// Słowo z literówką pasuje do słowa z tekstu (albo do jego początku: "brunh" ≈ "brunch", "louvr" ≈ "louvre").
function fuzzyWord(w: string, tokens: string[]): boolean {
  if (w.length < 4) return false;
  const max = w.length >= 7 ? 2 : 1;
  return tokens.some((t) => t.length >= w.length - max &&
    (editDist(w, t, max) <= max || (t.length > w.length && editDist(w, t.slice(0, w.length), max) <= max)));
}

export function searchItems(items: Item[], query: string): Item[] {
  const q = query.trim().toLowerCase();
  if (q.length < 2) return [];
  // Każde słowo musi pasować gdzieś w pozycji ("food festival" znajdzie festiwal jedzenia),
  // a końcówki liczby mnogiej nie przeszkadzają ("festivals" = "festival").
  const words = q.split(/\s+/).filter((w) => w.length >= 2).map((w) => (w.length > 4 ? w.replace(/(es|s)$/, '') : w));
  const hayOf = (i: Item) => [i.title, i.where, i.description, i.look.label, i.city, i.priceText].map((t) => (t ?? '').toLowerCase()).join(' | ');
  const exact = items.filter((i) => { const hay = hayOf(i); return words.every((w) => hay.includes(w)); });
  if (exact.length >= 3) return exact;
  // Mało wyników: dokładamy pozycje z literówką (tylko tytuł, miejsce i kategoria, żeby było szybko).
  const extra = items.filter((i) => {
    if (exact.includes(i)) return false;
    const hay = hayOf(i);
    const tokens = [i.title, i.where, i.look.label].join(' ').toLowerCase().split(/[^a-z0-9\u00c0-\u024f]+/).filter((t) => t.length >= 3);
    return words.every((w) => hay.includes(w) || fuzzyWord(w, tokens));
  });
  return [...exact, ...extra];
}

/** "Before or after": 2–3 oferty (happy hour, kolacja, wieczór) w tej samej dzielnicy w dniu eventu. */
const NEARBY_TYPES = new Set(['happy_hour', 'dinner', 'night_out', 'ladies_night']);
export function nearbyDeals(ev: Item, all: Item[], max = 3): Item[] {
  if (ev.kind !== 'event' || !ev.event) return [];
  const today = todayIso();
  const day = ev.event.start_date > today ? ev.event.start_date : today;
  const [y, m, d] = day.split('-').map(Number);
  const dow = new Date(y, m - 1, d).getDay();
  const near = (x: Item) => {
    if (ev.geo && x.geo) return distanceKm(ev.geo, x.geo) <= 3;
    return !!ev.zone && x.zone === ev.zone;
  };
  return all
    .filter((x) => x.kind === 'deal' && x.city === ev.city && NEARBY_TYPES.has(x.catKey) && !!x.deal && dealOnDay(x.deal, dow) && near(x))
    .sort((a, b) => (ev.geo && a.geo && b.geo ? distanceKm(ev.geo, a.geo) - distanceKm(ev.geo, b.geo) : 0))
    .slice(0, max);
}
