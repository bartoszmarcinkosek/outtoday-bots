// Połączenie z bazą Supabase.
// SUPABASE_KEY to klucz publiczny (publishable / anon). Jest bezpieczny w apce,
// bo baza pozwala nim tylko czytać zatwierdzone wpisy.
export const SUPABASE_URL = 'https://ibpuispeimyyqiailjfy.supabase.co';
export const SUPABASE_KEY = 'sb_publishable_2SPY_zl7rAw7K5D1T2TzwQ_mxpzYrCS';

// Adres, na który trafiają zgłoszenia z przycisku "Report a problem".
// Na razie pusty: telefon otworzy pustą wiadomość, adres wpiszesz ręcznie.
export const REPORT_EMAIL = 'outtodayapp@gmail.com';

// Znacznik "New" dostają tylko wpisy dodane po tej dacie (i nie starsze niż 7 dni).
export const NEW_BASELINE = '2026-11-16';
