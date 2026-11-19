// Anonimowy licznik: które zakładki/kategorie są używane. Bez identyfikatora urządzenia, lokalizacji i danych osobowych.
// Włączamy (STATS_ON = true) dopiero po zatwierdzeniu testu przez Google i dopisaniu tego w Data safety + polityce prywatności.
import { Platform } from 'react-native';
import { SUPABASE_KEY, SUPABASE_URL } from './config';

export const STATS_ON = false;

type Name = 'open' | 'tab' | 'item' | 'share' | 'new' | 'report' | 'plan' | 'interests' | 'suggest' | 'search' | 'filter' | 'map';

export function count(name: Name, value?: string | null, city?: string | null): void {
  if (!STATS_ON) return;
  const platform = Platform.OS === 'ios' || Platform.OS === 'android' ? Platform.OS : 'web';
  fetch(`${SUPABASE_URL}/rest/v1/app_stats`, {
    method: 'POST',
    headers: { apikey: SUPABASE_KEY, Authorization: `Bearer ${SUPABASE_KEY}`, 'Content-Type': 'application/json', Prefer: 'return=minimal' },
    body: JSON.stringify({ name, value: value ? String(value).slice(0, 60) : null, city: city ? city.slice(0, 30) : null, platform }),
  }).catch(() => undefined); // licznik nigdy nie przeszkadza w działaniu apki
}
