-- OutToday: tabele i kolumny dla botów (wersja 1)
-- Wklej całość w Supabase > SQL Editor i kliknij Run.
-- Skrypt można uruchomić ponownie bez szkody. Nie zmienia istniejących wpisów.

-- 1. Nowe kolumny w events: skąd bot to wziął i czego brakuje
alter table public.events add column if not exists bot_key      text;   -- odcisk wpisu, żeby nie dodawać dwa razy
alter table public.events add column if not exists evidence     jsonb;  -- dosłowne cytaty ze strony źródłowej
alter table public.events add column if not exists gaps         text[]; -- czego brakuje (np. price, start_time)
alter table public.events add column if not exists last_seen_at timestamptz; -- kiedy bot ostatnio widział wpis na stronie

create unique index if not exists events_bot_key_idx on public.events (bot_key);

-- 2. Strony sprawdzane przez boty (do porównania, czy coś się zmieniło)
create table if not exists public.bot_pages (
  url             text primary key,
  content_hash    text,
  last_fetched_at timestamptz,
  last_status     text,
  created_at      timestamptz not null default now()
);

-- 3. Zmiany wykryte w już istniejących wpisach (np. nowa cena) do porannego e-maila
create table if not exists public.bot_changes (
  id          uuid primary key default gen_random_uuid(),
  table_name  text not null,
  row_id      uuid not null,
  field       text not null,
  old_value   text,
  new_value   text,
  evidence    text,
  source_url  text,
  handled     boolean not null default false,
  created_at  timestamptz not null default now()
);

-- 4. Dziennik uruchomień
create table if not exists public.bot_runs (
  id          uuid primary key default gen_random_uuid(),
  started_at  timestamptz not null default now(),
  finished_at timestamptz,
  dry_run     boolean not null default true,
  summary     jsonb
);

-- 5. Zabezpieczenia: apka tych tabel nie widzi, tylko boty i panel (service_role)
alter table public.bot_pages   enable row level security;
alter table public.bot_changes enable row level security;
alter table public.bot_runs    enable row level security;
grant all on public.bot_pages, public.bot_changes, public.bot_runs to service_role;
