// Ciemny motyw: granatowe tło, karty w przygaszonych kolorach kategorii.
export const colors = {
  bg: '#0D1B33',
  surface: '#132544',
  chip: '#1B2D4F',
  primary: '#8FB4FF',
  text: '#EAF1FF',
  muted: '#9FB3D6',
  border: '#24385C',
  free: '#7CF0C0',
  errorBg: '#5A1A1D',
  errorText: '#FFD0D2',
};

export type CategoryStyle = {
  label: string;
  card: string; // tło karty
  title: string; // tytuł na karcie
  sub: string; // tekst pomocniczy na karcie
  accent: string; // etykieta, filtr, przycisk
};

// Każda kategoria ma własny kolor. Żeby go zmienić, popraw wartości w jednej linii.
export const categories: Record<string, CategoryStyle> = {
  // Events
  music: { label: 'Music & Shows', card: '#46308F', title: '#F0EBFF', sub: '#CFC2FF', accent: '#C0B0FF' },
  culture: { label: 'Culture & Art', card: '#1C3A7A', title: '#EAF1FF', sub: '#B7CEFF', accent: '#A9C6FF' },
  sport: { label: 'Sport & Fitness', card: '#0F5A44', title: '#E6FBF3', sub: '#A8E8D0', accent: '#8FE3C3' },
  food: { label: 'Food & Drinks', card: '#7A2327', title: '#FFECEC', sub: '#FFC4C6', accent: '#FFB3B6' },
  festivals: { label: 'Festivals', card: '#7A1F5C', title: '#FFEAF6', sub: '#FFBFE3', accent: '#FFADDB' },
  nightlife: { label: 'Nightlife', card: '#5A1E86', title: '#F6EBFF', sub: '#DDBFFF', accent: '#D2ABFF' },
  classes: { label: 'Classes & Workshops', card: '#6B4A00', title: '#FFF6E0', sub: '#FFE2A6', accent: '#FFD98A' },
  nature: { label: 'Nature & Outdoors', card: '#3A5F0E', title: '#F0FADF', sub: '#CDEBA0', accent: '#BFE38A' },
  community: { label: 'Community & Business', card: '#7A3A0C', title: '#FFF0E5', sub: '#FFCFAD', accent: '#FFBE94' },
  // Places
  beaches: { label: 'Beaches & Pools', card: '#0B5F68', title: '#E3FAFC', sub: '#A5E6EC', accent: '#8FDEE6' },
  parks: { label: 'Parks & Nature', card: '#3A5F0E', title: '#F0FADF', sub: '#CDEBA0', accent: '#BFE38A' },
  museums: { label: 'Museums & Culture', card: '#1C3A7A', title: '#EAF1FF', sub: '#B7CEFF', accent: '#A9C6FF' },
  attractions: { label: 'Attractions', card: '#7A1F5C', title: '#FFEAF6', sub: '#FFBFE3', accent: '#FFADDB' },
  active: { label: 'Sport & Active', card: '#0F5A44', title: '#E6FBF3', sub: '#A8E8D0', accent: '#8FE3C3' },
  kids: { label: 'Kids & Play', card: '#6B4A00', title: '#FFF6E0', sub: '#FFE2A6', accent: '#FFD98A' },
  markets: { label: 'Markets & Malls', card: '#7A3A0C', title: '#FFF0E5', sub: '#FFCFAD', accent: '#FFBE94' },
  studios: { label: 'Classes & Studios', card: '#5A1E86', title: '#F6EBFF', sub: '#DDBFFF', accent: '#D2ABFF' },
  daytrips: { label: 'Day Trips', card: '#33425A', title: '#EDF2F9', sub: '#C2CEDF', accent: '#B3C1D6' },
  // Stare klucze: zostają, żeby apka działała także przed uruchomieniem 05_categories.sql.
  family: { label: 'Family', card: '#6B4A00', title: '#FFF6E0', sub: '#FFE2A6', accent: '#FFD98A' },
  festival: { label: 'Festivals', card: '#7A1F5C', title: '#FFEAF6', sub: '#FFBFE3', accent: '#FFADDB' },
  market: { label: 'Markets', card: '#0B5F68', title: '#E3FAFC', sub: '#A5E6EC', accent: '#8FDEE6' },
  business: { label: 'Business', card: '#33425A', title: '#EDF2F9', sub: '#C2CEDF', accent: '#B3C1D6' },
};

// Typy promocji w zakładce Deals. Kolory dobrane tak, żeby różniły się od siebie.
export const dealTypes: Record<string, CategoryStyle> = {
  day_pass: { label: 'Day pass', card: '#0B5F68', title: '#E3FAFC', sub: '#A5E6EC', accent: '#8FDEE6' },
  ladies_night: { label: "Ladies' night", card: '#7A1F5C', title: '#FFEAF6', sub: '#FFBFE3', accent: '#FFADDB' },
  brunch: { label: 'Brunch', card: '#6B4A00', title: '#FFF6E0', sub: '#FFE2A6', accent: '#FFD98A' },
  happy_hour: { label: 'Happy hour', card: '#7A3A0C', title: '#FFF0E5', sub: '#FFCFAD', accent: '#FFBE94' },
  night_out: { label: 'Nights out', card: '#5A1E86', title: '#F6EBFF', sub: '#DDBFFF', accent: '#D2ABFF' },
  lunch: { label: 'Business lunch', card: '#0F5A44', title: '#E6FBF3', sub: '#A8E8D0', accent: '#8FE3C3' },
  dinner: { label: 'Dinner deals', card: '#7A2327', title: '#FFECEC', sub: '#FFC4C6', accent: '#FFB3B6' },
  quiz: { label: 'Quiz night', card: '#46308F', title: '#F0EBFF', sub: '#CFC2FF', accent: '#C0B0FF' },
};
export const DEAL_TYPE_ORDER = ['day_pass', 'brunch', 'ladies_night', 'happy_hour', 'night_out', 'quiz', 'lunch', 'dinner'];

export function dealStyle(key: string | null | undefined): CategoryStyle {
  return dealTypes[key ?? ''] ?? { ...fallback, label: 'Other deal' };
}

const fallback: CategoryStyle = { label: 'Other', card: '#33425A', title: '#EDF2F9', sub: '#C2CEDF', accent: '#B3C1D6' };

export function cat(key: string | null | undefined): CategoryStyle {
  const found = categories[key ?? ''];
  return found ?? { ...fallback, label: key ?? 'Other' };
}
