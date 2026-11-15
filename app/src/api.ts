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
  name: string;
  description: string | null;
  category: string;
  area: string | null;
  city: string;
  hours_text: string | null;
  price_text: string | null;
  is_free: boolean;
  kid_friendly?: boolean;
  is_indoor?: boolean;
  pet_friendly?: boolean;
  ladies_only?: boolean;
  official_url?: string | null;
  phone?: string | null;
  created_at?: string | null;
  updated_at?: string | null;

  url: string | null;
  source_name: string | null;
};

export type DealRow = {
  id: string;
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
  phone?: string | null;
  created_at?: string | null;
  updated_at?: string | null;

  url: string | null;
  source_name: string | null;
};

export type AppData = { events: EventRow[]; places: PlaceRow[]; deals: DealRow[]; fetchedAt: string };

const CACHE_KEY = 'outtoday.data.v1';

async function getTable<T>(table: string, order: string): Promise<T[]> {
  const res = await fetch(`${SUPABASE_URL}/rest/v1/${table}?select=*&order=${order}`, {
    headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}` },
  });
  if (!res.ok) {
    throw new Error(`${table}: ${res.status} ${await res.text()}`);
  }
  return (await res.json()) as T[];
}

export async function loadCached(): Promise<AppData | null> {
  try {
    const raw = await AsyncStorage.getItem(CACHE_KEY);
    return raw ? (JSON.parse(raw) as AppData) : null;
  } catch {
    return null;
  }
}

export async function fetchAll(): Promise<AppData> {
  const [events, places, deals] = await Promise.all([
    getTable<EventRow>('events', 'start_date.asc,start_time.asc.nullslast'),
    getTable<PlaceRow>('places', 'name.asc'),
    getTable<DealRow>('deals', 'title.asc'),
  ]);
  const data: AppData = { events, places, deals, fetchedAt: new Date().toISOString() };
  try {
    await AsyncStorage.setItem(CACHE_KEY, JSON.stringify(data));
  } catch {
    // Brak pamięci podręcznej nie blokuje działania apki.
  }
  return data;
}
