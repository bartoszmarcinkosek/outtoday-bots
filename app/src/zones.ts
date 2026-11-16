// Rejony miasta. Rejon rozpoznajemy po słowach w nazwie miejsca i w polu "area".
// Kolejność ma znaczenie: pierwsze dopasowanie wygrywa.
export type Zone = { city: string; key: string; label: string; match: string[] };

// Rejony każdego miasta. Rejon rozpoznajemy po słowach w nazwie miejsca i w polu "area",
// ale tylko wśród rejonów miasta danej pozycji (np. "Corniche" jest i w Abu Dhabi, i w Ajmanie).
// Kolejność ma znaczenie: pierwsze dopasowanie wygrywa.
export const ZONES: Zone[] = [
  { city: 'Al Ain', key: 'alain', label: 'Al Ain', match: ['al ain', 'jebel haf', 'mubazzarah', 'qattara', 'al jimi'] },
  { city: 'Abu Dhabi', key: 'dhafra', label: 'Al Dhafra', match: ['dhafra', 'liwa', 'mirfa', 'marfa', 'dalma island', 'madinat zayed city'] },
  { city: 'Abu Dhabi', key: 'saadiyat', label: 'Saadiyat Island', match: ['saadiyat', 'louvre', 'mamsha', 'guggenheim', 'nyu abu dhabi', 'zayed national museum', 'natural history museum'] },
  { city: 'Abu Dhabi', key: 'yas', label: 'Yas Island', match: ['yas ', 'yas,', 'etihad arena', 'etihad park', 'etihad live', 'ferrari world', 'warner bros', 'the wb', 'seaworld'] },
  { city: 'Abu Dhabi', key: 'hudayriyat', label: 'Hudayriyat', match: ['hudayriyat', 'hudayriat', 'bab al nojoum'] },
  { city: 'Abu Dhabi', key: 'maryah', label: 'Al Maryah Island', match: ['maryah', 'galleria', 'rosewood', 'four seasons'] },
  { city: 'Abu Dhabi', key: 'reem', label: 'Reem Island', match: ['reem'] },
  { city: 'Abu Dhabi', key: 'mina', label: 'Mina Zayed', match: ['mina', 'miza', 'zayed port', '421'] },
  { city: 'Abu Dhabi', key: 'maqta', label: 'Khor Al Maqta', match: ['wahat al karama', 'park rotana', 'maqta', 'qaryat al beri', 'atlon', 'bab al bahr', 'rabdan', 'al qana', 'grand canal', 'grand mosque', 'erth'] },
  { city: 'Abu Dhabi', key: 'corniche', label: 'Corniche', match: ['grand hyatt', 'sheraton abu dhabi', 'corniche', 'etihad towers', 'emirates palace', 'ras al akhdar', 'marina mall', 'al marina', 'nation towers', 'khubairah'] },
  { city: 'Abu Dhabi', key: 'bateen', label: 'Al Bateen', match: ['bateen'] },
  { city: 'Abu Dhabi', key: 'downtown', label: 'Downtown', match: ['le meridien', 'cristal hotel', 'dusit thani', 'mohammed bin zayed stadium', 'al hosn', 'cultural foundation', 'al danah', 'markaziya', 'zahiyah', 'khalidiya', 'khalidiyah', 'trade cent', 'wtc', 'hamdan', 'al manhal', 'al wahda', 'mushrif', 'umm al emarat', 'al nahyan', 'rawdah', 'al zahiyah'] },
  { city: 'Abu Dhabi', key: 'adnec', label: 'ADNEC & Capital', match: ['adnec', 'capital gate', 'capital centre', 'zayed sports city'] },
  { city: 'Abu Dhabi', key: 'mainland', label: 'Mainland & Suburbs', match: ['zayed cricket stadium', 'al ghazal', 'mussafah', 'musaffah', 'masdar', 'khalifa city', 'al raha', 'al forsan', 'wathba', 'jubail', 'baniyas', 'al bahia', 'mangrove', 'khalifa park'] },
  // Dubai
  { city: 'Dubai', key: 'dxb_palm', label: 'Palm Jumeirah', match: ['palm jumeirah', 'atlantis', 'the pointe', 'nakheel mall'] },
  { city: 'Dubai', key: 'dxb_marina', label: 'Dubai Marina & JBR', match: ['dubai marina', 'marina walk', 'jbr', 'the beach', 'bluewaters', 'ain dubai', 'skydive dubai', 'dubai harbour', 'al sufouh', 'media city', 'media one', 'dubai college', 'bla bla'] },
  { city: 'Dubai', key: 'dxb_downtown', label: 'Downtown & Business Bay', match: ['downtown', 'burj khalifa', 'dubai mall', 'dubai opera', 'souk al bahar', 'business bay', 'difc', 'dubai water canal', 'museum of the future', 'world trade centre', 'sheikh zayed road', 'time out market'] },
  { city: 'Dubai', key: 'dxb_oldtown', label: 'Deira & Bur Dubai', match: ['deira', 'bur dubai', 'al fahidi', 'al seef', 'gold souk', 'spice souk', 'karama', 'dubai frame', 'zabeel', 'creek park', 'oud metha', 'oud mehta', 'ihs', 'garhoud', 'irish village', 'le meridien dubai hotel', 'theatre by qe2', 'queen elizabeth 2', 'mina rashid', 'port rashid'] },
  { city: 'Dubai', key: 'dxb_creek', label: 'Creek Harbour & Festival City', match: ['creek harbour', 'festival city', 'ras al khor', 'jaddaf', 'jameel arts', 'culture village', 'festival bay'] },
  { city: 'Dubai', key: 'dxb_quoz', label: 'Al Quoz & Al Barsha', match: ['al quoz', 'alserkal', 'al barsha', 'mall of the emirates', 'ski dubai', 'courtyard playhouse', 'the junction', 'dubai heights academy'] },
  { city: 'Dubai', key: 'dxb_jumeirah', label: 'Jumeirah & City Walk', match: ['jumeirah', 'la mer', 'kite beach', 'city walk', 'burj al arab', 'madinat jumeirah', 'umm suqeim', 'al wasl road', 'coca-cola arena', 'sunset beach', 'jumeira ', 'jumeira,', 'theatre of digital art', 'toda'] },
  { city: 'Dubai', key: 'dxb_hills', label: 'Dubai Hills & Al Khail', match: ['dubai hills', 'meydan', 'al khail', 'motor city', 'sports city', 'global village', 'arabian ranches', 'al habtoor polo', 'damac hills'] },
  { city: 'Dubai', key: 'dxb_south', label: 'Expo City & Dubai South', match: ['expo city', 'al wasl plaza', 'jubilee park', 'terra, ', 'surreal', 'dubai south', 'jebel ali', 'dubai parks', 'legoland', 'motiongate', 'jafza', 'riverland'] },
  { city: 'Dubai', key: 'dxb_hatta', label: 'Hatta', match: ['hatta'] },
  // Sharjah
  { city: 'Sharjah', key: 'shj_center', label: 'Al Majaz & Al Qasba', match: ['majaz', 'qasba', 'khalid lagoon', 'al noor island', 'buhaira'] },
  { city: 'Sharjah', key: 'shj_heritage', label: 'Heart of Sharjah', match: ['heart of sharjah', 'heritage area', 'arts area', 'mureijah', 'bait obaid', 'sharjah art foundation', 'al shuwaihean', 'museum of islamic civilization', 'souq al arsah'] },
  { city: 'Sharjah', key: 'shj_aljada', label: 'Aljada & University City', match: ['aljada', 'university city', 'al rahmaniya'] },
  { city: 'Sharjah', key: 'shj_mleiha', label: 'Mleiha', match: ['mleiha'] },
  { city: 'Sharjah', key: 'shj_east', label: 'Khor Fakkan & Kalba', match: ['khor fakkan', 'kalba', 'dibba al hisn'] },
  // Pozostałe emiraty na razie jako jeden rejon każdy
  { city: 'Ajman', key: 'ajm', label: 'Ajman', match: ['ajman'] },
  { city: 'Umm Al Quwain', key: 'uaq', label: 'Umm Al Quwain', match: ['umm al quwain', 'umm al qaiwain'] },
  { city: 'Ras Al Khaimah', key: 'rak', label: 'Ras Al Khaimah', match: ['ras al khaimah', 'jebel jais', 'al marjan', 'al hamra', 'rak'] },
  { city: 'Fujairah', key: 'fuj', label: 'Fujairah', match: ['fujairah', 'dibba', 'al aqah', 'snoopy island', 'masafi'] },
];

export const CITIES = ['Abu Dhabi', 'Al Ain', 'Dubai', 'Sharjah', 'Ajman', 'Umm Al Quwain', 'Ras Al Khaimah', 'Fujairah'];

export const CITY_CENTER: Record<string, [number, number, number]> = {
  // szerokość, długość, zoom mapy (stopnie)
  'Abu Dhabi': [24.46, 54.47, 0.42],
  'Al Ain': [24.2075, 55.7447, 0.35],
  Dubai: [25.15, 55.25, 0.5],
  Sharjah: [25.33, 55.45, 0.4],
  Ajman: [25.405, 55.5136, 0.15],
  'Umm Al Quwain': [25.5647, 55.5552, 0.2],
  'Ras Al Khaimah': [25.8, 55.98, 0.4],
  Fujairah: [25.13, 56.33, 0.4],
};

function normalizeCity(raw: string | null | undefined): string {
  const c = (raw ?? '').toLowerCase();
  if (c.includes('al ain')) return 'Al Ain';
  if (c.includes('dubai')) return 'Dubai';
  if (c.includes('sharjah')) return 'Sharjah';
  if (c.includes('ajman')) return 'Ajman';
  if (c.includes('umm al')) return 'Umm Al Quwain';
  if (c.includes('ras al khaimah') || c === 'rak') return 'Ras Al Khaimah';
  if (c.includes('fujairah')) return 'Fujairah';
  return 'Abu Dhabi';
}

// Miasto i rejon pozycji. Al Ain leży w emiracie Abu Dhabi, więc pozycje zapisane jako
// "Abu Dhabi", ale z adresem w Al Ain, trafiają do Al Ain.
export function placeOf(cityRaw: string | null | undefined, ...parts: (string | null | undefined)[]): { city: string; zone: string | null } {
  const city = normalizeCity(cityRaw);
  const text = ` ${parts.filter(Boolean).join(' , ').toLowerCase()} `;
  const pool = ZONES.filter((z) => z.city === city || (city === 'Abu Dhabi' && z.city === 'Al Ain'));
  pool.sort((a, b) => Number(b.city === 'Al Ain') - Number(a.city === 'Al Ain'));
  for (const z of pool) {
    if (z.match.some((m) => text.includes(m))) return { city: z.city, zone: z.key };
  }
  // Emiraty z jednym rejonem: każda pozycja z tego miasta należy do niego.
  const single = ZONES.filter((z) => z.city === city);
  return { city, zone: single.length === 1 ? single[0].key : null };
}

// Przybliżony środek każdego rejonu. Służy do liczenia odległości "około X km",
// dopóki w bazie nie ma dokładnych współrzędnych miejsc.
export const ZONE_CENTER: Record<string, [number, number]> = {
  alain: [24.2075, 55.7447],
  dhafra: [23.6539, 53.7042],
  saadiyat: [24.5393, 54.4325],
  yas: [24.4887, 54.6072],
  hudayriyat: [24.4216, 54.3492],
  maryah: [24.5022, 54.3897],
  reem: [24.4955, 54.4055],
  mina: [24.5215, 54.3775],
  maqta: [24.4105, 54.4905],
  corniche: [24.4705, 54.3345],
  bateen: [24.4515, 54.3515],
  downtown: [24.4815, 54.3705],
  adnec: [24.4185, 54.4385],
  mainland: [24.4005, 54.6005],
  dxb_palm: [25.1124, 55.139],
  dxb_marina: [25.08, 55.14],
  dxb_downtown: [25.195, 55.274],
  dxb_oldtown: [25.263, 55.302],
  dxb_creek: [25.205, 55.345],
  dxb_quoz: [25.13, 55.22],
  dxb_jumeirah: [25.2, 55.245],
  dxb_hills: [25.08, 55.26],
  dxb_south: [24.96, 55.12],
  dxb_hatta: [24.8, 56.12],
  shj_center: [25.325, 55.385],
  shj_heritage: [25.36, 55.385],
  shj_aljada: [25.31, 55.48],
  shj_mleiha: [25.127, 55.878],
  shj_east: [25.339, 56.356],
  ajm: [25.405, 55.5136],
  uaq: [25.5647, 55.5552],
  rak: [25.8, 55.98],
  fuj: [25.13, 56.33],
};



export function distanceKm(a: [number, number], b: [number, number]): number {
  const rad = (x: number) => (x * Math.PI) / 180;
  const dLat = rad(b[0] - a[0]);
  const dLon = rad(b[1] - a[1]);
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(rad(a[0])) * Math.cos(rad(b[0])) * Math.sin(dLon / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(h));
}
