import AsyncStorage from '@react-native-async-storage/async-storage';
import { SUPABASE_KEY, SUPABASE_URL } from './config';

export type EventRow = {
  id: string;
  title: string;
  description: string | null;
  category: string;
  start_date: string;
  end_date: string | null;
  start_time: string | null;
  end_time: string | null;
  venue: string | null;
  area: string | null;
  city: string;
  price_text: string | null;
  is_free: boolean;
  kid_friendly?: boolean;
  price_min_aed?: number | null;
  pet_friendly?: boolean;
  ladies_only?: boolean;
  official_url?: string | null;
  lat?: number | null;
  lng?: number | null;
  phone?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  registration_required: boolean;
  url: string | null;
  source_name: string | null;
  source_url: string | null;
  verified_at: string | null;
};

export type PlaceRow = {
  id: string;
  verified_at?: string | null;
  name: string;
  description: string | null;
  category: string;
  area: string | null;
  city: string;
  hours_text: string | null;
  hours?: Record<string, string[][]> | null; // 0 = niedziela, [["10:00","22:00"]]
  price_text: string | null;
  is_free: boolean;
  kid_friendly?: boolean;
  is_indoor?: boolean;
  pet_friendly?: boolean;
  ladies_only?: boolean;
  official_url?: string | null;
  lat?: number | null;
  lng?: number | null;
  phone?: string | null;
  created_at?: string | null;
  updated_at?: string | null;

  url: string | null;
  source_name: string | null;
};

export type DealRow = {
  id: string;
  verified_at?: string | null;
  deal_type: string | null;
  title: string;
  details: string | null;
  venue: string | null;
  area: string | null;
  city: string;
  days_of_week: number[] | null;
  start_time: string | null;
  end_time: string | null;
  price_text: string | null;
  valid_until: string | null;
  kid_friendly?: boolean;
  pet_friendly?: boolean;
  ladies_only?: boolean;
  official_url?: string | null;
  lat?: number | null;
  lng?: number | null;
  phone?: string | null;
  created_at?: string | null;
  updated_at?: string | null;

  url: string | null;
  source_name: string | null;
};

export type AppData = { events: EventRow[]; places: PlaceRow[]; deals: DealRow[]; fetchedAt: string };

const CACHE_KEY = 'outtoday.data.v1';

// Tylko potrzebne kolumny (bez "evidence" itp.), stronami po 1000 – Supabase oddaje najwyżej 1000 wierszy naraz.
async function getTable<T>(table: string, order: string, select: string, extra = ''): Promise<T[]> {
  const out: T[] = [];
  for (let from = 0; from < 20000; from += 1000) {
    const res = await fetch(`${SUPABASE_URL}/rest/v1/${table}?select=${select}&order=${order}${extra}`, {
      headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}`, Range: `${from}-${from + 999}` },
    });
    if (!res.ok) {
      throw new Error(`${table}: ${res.status} ${await res.text()}`);
    }
    const page = (await res.json()) as T[];
    out.push(...page);
    if (page.length < 1000) break;
  }
  return out;
}

const EVENT_COLS = 'id,title,description,category,start_date,end_date,start_time,end_time,venue,area,city,price_text,is_free,kid_friendly,price_min_aed,pet_friendly,ladies_only,official_url,lat,lng,phone,created_at,updated_at,registration_required,url,source_name,source_url,verified_at';
const PLACE_COLS = 'id,name,description,category,area,city,hours_text,hours,price_text,is_free,kid_friendly,is_indoor,pet_friendly,ladies_only,official_url,lat,lng,phone,created_at,updated_at,url,source_name,verified_at';
const DEAL_COLS = 'id,deal_type,title,details,venue,area,city,days_of_week,start_time,end_time,price_text,valid_until,kid_friendly,pet_friendly,ladies_only,official_url,lat,lng,phone,created_at,updated_at,url,source_name,verified_at';

// Zapis w kawałkach po ~500 KB: na Androidzie jedna wartość powyżej ~2 MB nie da się odczytać,
// a cała baza jest już większa. Dzięki temu apka startuje od razu z ostatnimi danymi.
const CHUNK = 500_000;

async function saveCache(data: AppData): Promise<void> {
  const raw = JSON.stringify(data);
  const parts: [string, string][] = [];
  for (let i = 0; i * CHUNK < raw.length; i++) parts.push([`${CACHE_KEY}:${i}`, raw.slice(i * CHUNK, (i + 1) * CHUNK)]);
  await AsyncStorage.multiSet([...parts, [`${CACHE_KEY}:n`, String(parts.length)]]);
  AsyncStorage.removeItem(CACHE_KEY).catch(() => undefined); // stary zapis w jednym kawałku
}

export async function loadCached(): Promise<AppData | null> {
  try {
    const n = Number(await AsyncStorage.getItem(`${CACHE_KEY}:n`));
    if (n > 0) {
      const got = await AsyncStorage.multiGet(Array.from({ length: n }, (_, i) => `${CACHE_KEY}:${i}`));
      if (got.every(([, v]) => v != null)) return JSON.parse(got.map(([, v]) => v).join('')) as AppData;
    }
    const raw = await AsyncStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as AppData) : null;
  } catch {
    return null;
  }
}

function todayUae(): string {
  return new Date(Date.now() + 4 * 3600000).toISOString().slice(0, 10); // data w ZEA (UTC+4)
}

export async function fetchAll(): Promise<AppData> {
  const [events, places, deals] = await Promise.all([
    // tylko eventy, które jeszcze trwają albo dopiero będą (minione nie są potrzebne)
    getTable<EventRow>('events', 'start_date.asc,start_time.asc.nullslast,id.asc', EVENT_COLS,
      `&or=(end_date.gte.${todayUae()},and(end_date.is.null,start_date.gte.${todayUae()}))`),
    getTable<PlaceRow>('places', 'name.asc,id.asc', PLACE_COLS),
    getTable<DealRow>('deals', 'title.asc,id.asc', DEAL_COLS),
  ]);
  const data: AppData = { events, places, deals, fetchedAt: new Date().toISOString() };
  try {
    await saveCache(data);
  } catch {
    // Brak pamięci podręcznej nie blokuje działania apki.
  }
  return data;
}

// Zgłoszenie eventu od użytkownika (tabela suggestions: apka może tylko dodawać).
export type Suggestion = { title: string; event_date?: string; venue?: string; city?: string; link?: string; note?: string; contact?: string };

export async function sendSuggestion(s: Suggestion): Promise<void> {
  const body = Object.fromEntries(Object.entries(s).map(([k, v]) => [k, (v ?? '').trim() || null]));
  const res = await fetch(`${SUPABASE_URL}/rest/v1/suggestions`, {
    method: 'POST',
    headers: {
      apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}`,
      'Content-Type': 'application/json', Prefer: 'return=minimal',
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${res.status}`);
}
