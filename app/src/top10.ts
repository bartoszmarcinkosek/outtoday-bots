// Top 10 miejsc w mieście – kolejność z oficjalnych stron turystyki (Visit Dubai, Visit Abu Dhabi,
// Visit Sharjah, Visit Ras Al Khaimah). Nazwy muszą być takie jak w bazie (tabela places).
// Miasta bez oficjalnej listy (Ajman, Fujairah, Umm Al Quwain) nie mają filtra Top 10.
export const TOP10: Record<string, string[]> = {
  Dubai: [
    'The Green Planet', 'Burj Khalifa: At the Top', 'Dubai Aquarium & Underwater Zoo', 'Dubai Frame',
    'The View at The Palm', 'Global Village', 'Museum of the Future', 'Topgolf Dubai', 'Ski Dubai', 'Dubai Miracle Garden',
  ],
  'Abu Dhabi': [
    'Qasr Al Watan', 'Sheikh Zayed Grand Mosque', 'Louvre Abu Dhabi', 'Ferrari World Abu Dhabi',
    'Warner Bros. World Abu Dhabi', 'Qasr Al Hosn fort museum', 'Jubail Mangrove Park', 'Emirates Palace public areas',
    'Corniche Beach (Gate 4)',
  ],
  Sharjah: [
    'Al Noor Island', 'Heart of Sharjah', 'Aljada', 'Al Majaz Waterfront', 'Al Qasba', 'Al Montazah Parks',
    'Sharjah Mosque', 'Rain Room Sharjah', 'Sharjah Archaeology Museum', 'Central Souk (Blue Souk)',
  ],
  'Ras Al Khaimah': [
    'Al Sawan Camel Race Track', 'Jebel Jais', 'Dhayah Fort', 'Al Rams Beach', 'Al Jazeera Al Hamra Heritage Village',
    'Mangrove kayaking (Al Qawasim Corniche)', 'Al Jazirah Aviation Club', 'Suwaidi Pearl Farm', 'Kuwaiti Souq',
  ],
  'Al Ain': [
    'Al Ain Oasis', 'Souq Al Zafarana', 'Wadi Adventure', 'Jebel Hafit', 'Qasr Al Muwaiji', 'Al Jahili Fort',
    'Jebel Hafit Desert Park', 'Al Ain Camel Market', 'Al Ain Zoo',
  ],
};

const norm = (s: string) => s.trim().toLowerCase();

/** Miejsce w rankingu (1–10) albo null. Sprawdza miasto miejsca, a dla Al Ain także Abu Dhabi (i odwrotnie). */
export function topRank(city: string, name: string): number | null {
  for (const c of [city, city === 'Abu Dhabi' ? 'Al Ain' : city === 'Al Ain' ? 'Abu Dhabi' : null]) {
    if (!c || !TOP10[c]) continue;
    const i = TOP10[c].findIndex((n) => norm(n) === norm(name));
    if (i >= 0) return i + 1;
  }
  return null;
}

export const hasTop10 = (city: string) => !!TOP10[city];
