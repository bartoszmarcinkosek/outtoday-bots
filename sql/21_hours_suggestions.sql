-- 1) "Open now": godziny otwarcia w formie tabeli (bot wypełnia z hours_text).
--    Format: {"0":[["10:00","22:00"]], ..., "6":[...]}  (0 = niedziela), {} gdy nie da się odczytać.
alter table public.places add column if not exists hours jsonb;

-- 2) "Suggest an event": zgłoszenia od użytkowników apki.
create table if not exists public.suggestions (
  id uuid primary key default gen_random_uuid(),
  created_at timestamptz not null default now(),
  title text not null check (char_length(title) between 3 and 150),
  event_date text check (char_length(event_date) <= 40),
  venue text check (char_length(venue) <= 150),
  city text check (char_length(city) <= 40),
  link text check (char_length(link) <= 400),
  note text check (char_length(note) <= 600),
  contact text check (char_length(contact) <= 120),
  status text not null default 'new'
);
alter table public.suggestions enable row level security;

-- apka może tylko DODAWAĆ zgłoszenia (nie może ich czytać, zmieniać ani kasować)
drop policy if exists "anyone can suggest" on public.suggestions;
create policy "anyone can suggest" on public.suggestions
  for insert to anon, authenticated
  with check (status = 'new');
grant insert on public.suggestions to anon, authenticated;
