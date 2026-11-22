// Prośba o ocenę w App Store / Google Play: raz, gdy ktoś realnie używa apki
// (co najmniej 5 otwartych wpisów w co najmniej 3 różne dni). System sam decyduje, czy okno pokazać.
import AsyncStorage from '@react-native-async-storage/async-storage';

const KEY = 'review_v1';
let StoreReview: { isAvailableAsync?: () => Promise<boolean>; requestReview?: () => Promise<void> } | null = null;
try {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  StoreReview = require('expo-store-review');
} catch {
  StoreReview = null; // starsza wersja apki bez modułu – nic nie robimy
}

type State = { opens: number; days: string[]; asked: boolean };

/** Wołane po otwarciu szczegółów wpisu. */
export async function noteItemOpened(): Promise<void> {
  try {
    const s: State = JSON.parse((await AsyncStorage.getItem(KEY)) ?? 'null') ?? { opens: 0, days: [], asked: false };
    if (s.asked) return;
    const today = new Date().toISOString().slice(0, 10);
    s.opens += 1;
    if (!s.days.includes(today)) s.days = [...s.days, today].slice(-10);
    if (s.opens >= 5 && s.days.length >= 3 && StoreReview?.isAvailableAsync && (await StoreReview.isAvailableAsync())) {
      s.asked = true;
      await AsyncStorage.setItem(KEY, JSON.stringify(s));
      setTimeout(() => { StoreReview?.requestReview?.().catch(() => undefined); }, 1500);
      return;
    }
    await AsyncStorage.setItem(KEY, JSON.stringify(s));
  } catch {
    // ocena nigdy nie może przeszkodzić w działaniu apki
  }
}
