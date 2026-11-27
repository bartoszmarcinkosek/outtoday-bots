// Automatyczne zgłaszanie błędów apki (decyzja właściciela 27.11.2026: „błędy apki – tak”).
// Błąd trafia do tabeli suggestions jako "AppError: ..." – bez danych osobowych (tylko system, wersja, treść błędu).
// Czyta je codzienne zadanie „błędy apki” (bot/diag_errors.py).
import { Platform } from 'react-native';
import * as Updates from 'expo-updates';
import { sendSuggestion } from './api';

const sent = new Set<string>();
let total = 0;

export function reportError(kind: string, err: unknown, extra?: string): void {
  try {
    const e = err instanceof Error ? err : new Error(String(err));
    const msg = (e.message || 'unknown').slice(0, 140);
    const key = `${kind}|${msg}`;
    if (sent.has(key) || total >= 5) return; // ten sam błąd raz na uruchomienie, najwyżej 5 zgłoszeń
    sent.add(key);
    total += 1;
    const env = `${Platform.OS} ${String(Platform.Version)} · runtime ${Updates.runtimeVersion ?? '?'} · update ${(Updates.updateId ?? 'embedded').slice(0, 8)}`;
    const note = [env, extra ?? '', (e.stack ?? '').split('\n').slice(0, 12).join('\n')].filter(Boolean).join('\n').slice(0, 1800);
    sendSuggestion({ title: `AppError: ${kind}: ${msg}`, note }).catch(() => undefined);
  } catch { /* zgłaszanie błędów nigdy nie może samo zepsuć apki */ }
}

type GlobalHandler = (error: unknown, isFatal?: boolean) => void;
export function installErrorReporting(): void {
  const EU = (globalThis as unknown as { ErrorUtils?: { getGlobalHandler: () => GlobalHandler; setGlobalHandler: (h: GlobalHandler) => void } }).ErrorUtils;
  if (!EU) return;
  const prev = EU.getGlobalHandler();
  EU.setGlobalHandler((error, isFatal) => {
    reportError(isFatal ? 'crash' : 'js', error);
    prev(error, isFatal);
  });
}
