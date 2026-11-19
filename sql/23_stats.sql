-- Anonimowy licznik użycia apki (bez identyfikatora urządzenia, bez lokalizacji, bez danych osobowych).
-- Apka może tylko DODAWAĆ wiersze; czytać mogą tylko boty (service_role) do podsumowania w mailu.
create table if not exists public.app_stats (
  id bigint generated always as identity primary key,
  day date not null default current_date,
  name text not null check (name in ('open', 'tab', 'item', 'share', 'new', 'suggest', 'search', 'filter', 'map')),
  value text check (char_length(value) <= 60),
  city text check (char_length(city) <= 30),
  platform text check (platform in ('ios', 'android', 'web'))
);
alter table public.app_stats enable row level security;
drop policy if exists "app can count" on public.app_stats;
create policy "app can count" on public.app_stats for insert to anon, authenticated with check (day = current_date);
grant insert on public.app_stats to anon, authenticated;
grant select, delete on public.app_stats to service_role;
create index if not exists app_stats_day on public.app_stats (day);
